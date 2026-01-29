"""UART Component for embhome."""

import logging

from esphome import pins
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.const import (
    CONF_BAUD_RATE,
    CONF_DATA_BITS,
    CONF_ID,
    CONF_NUMBER,
    CONF_PARITY,
    CONF_RX_BUFFER_SIZE,
    CONF_RX_PIN,
    CONF_STOP_BITS,
    CONF_TX_PIN,
    CONF_UART_ID,
    PLATFORM_ESP32,
)
from esphome.core import CoroPriority, coroutine_with_priority
import esphome.final_validate as fv

_LOGGER = logging.getLogger(__name__)
CODEOWNERS = ["@esphome/core"]
MULTI_CONF = True

uart_ns = cg.esphome_ns.namespace("uart")
UARTComponent = uart_ns.class_("UARTComponent", cg.Component)
UARTDevice = uart_ns.class_("UARTDevice")

UARTParityOptions = uart_ns.enum("UARTParityOptions")
UART_PARITY_OPTIONS = {
    "NONE": UARTParityOptions.UART_CONFIG_PARITY_NONE,
    "EVEN": UARTParityOptions.UART_CONFIG_PARITY_EVEN,
    "ODD": UARTParityOptions.UART_CONFIG_PARITY_ODD,
}

CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(UARTComponent),
            cv.Required(CONF_BAUD_RATE): cv.int_range(min=1),
            cv.Optional(CONF_TX_PIN): pins.internal_gpio_output_pin_schema,
            cv.Optional(CONF_RX_PIN): pins.internal_gpio_input_pin_schema,
            cv.Optional(CONF_RX_BUFFER_SIZE, default=256): cv.validate_bytes,
            cv.Optional(CONF_STOP_BITS, default=1): cv.one_of(1, 2, int=True),
            cv.Optional(CONF_DATA_BITS, default=8): cv.int_range(min=5, max=8),
            cv.Optional(CONF_PARITY, default="NONE"): cv.enum(
                UART_PARITY_OPTIONS, upper=True
            ),
        }
    ).extend(cv.COMPONENT_SCHEMA),
    cv.has_at_least_one_key(CONF_TX_PIN, CONF_RX_PIN),
    cv.only_on([PLATFORM_ESP32]),
)


@coroutine_with_priority(CoroPriority.BUS)
async def to_code(config):
    """Generate code for UART component."""
    cg.add_global(uart_ns.using)
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)

    cg.add(var.set_baud_rate(config[CONF_BAUD_RATE]))

    if CONF_TX_PIN in config:
        cg.add(var.set_tx_pin(config[CONF_TX_PIN][CONF_NUMBER]))
    if CONF_RX_PIN in config:
        cg.add(var.set_rx_pin(config[CONF_RX_PIN][CONF_NUMBER]))

    cg.add(var.set_rx_buffer_size(config[CONF_RX_BUFFER_SIZE]))
    cg.add(var.set_stop_bits(config[CONF_STOP_BITS]))
    cg.add(var.set_data_bits(config[CONF_DATA_BITS]))
    cg.add(var.set_parity(config[CONF_PARITY]))


UART_DEVICE_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_UART_ID): cv.use_id(UARTComponent),
    }
)


async def register_uart_device(var, config):
    """Register a UART device.

    This is a coroutine, you need to await it with an 'await' expression!
    """
    parent = await cg.get_variable(config[CONF_UART_ID])
    cg.add(var.set_uart_parent(parent))


def final_validate_device_schema(
    name: str,
    *,
    baud_rate: int = None,
    require_tx: bool = False,
    require_rx: bool = False,
):
    """Validate device-specific UART requirements."""

    def validate_baud_rate(value):
        if value != baud_rate:
            raise cv.Invalid(
                f"Component {name} requires baud rate {baud_rate} for the UART bus"
            )
        return value

    def validate_hub(hub_config):
        hub_schema = {}

        if require_tx:
            hub_schema[
                cv.Required(
                    CONF_TX_PIN,
                    msg=f"Component {name} requires UART to declare a tx_pin",
                )
            ] = cv.valid
        if require_rx:
            hub_schema[
                cv.Required(
                    CONF_RX_PIN,
                    msg=f"Component {name} requires UART to declare a rx_pin",
                )
            ] = cv.valid

        if baud_rate is not None:
            hub_schema[cv.Required(CONF_BAUD_RATE)] = validate_baud_rate

        return cv.Schema(hub_schema, extra=cv.ALLOW_EXTRA)(hub_config)

    return cv.Schema(
        {cv.Required(CONF_UART_ID): fv.id_declaration_match_schema(validate_hub)},
        extra=cv.ALLOW_EXTRA,
    )
