"""
I2C Bus Component for embhome.

This component provides I2C bus communication support.
"""

import logging

from esphome import pins
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.const import (
    CONF_ADDRESS,
    CONF_FREQUENCY,
    CONF_I2C,
    CONF_I2C_ID,
    CONF_ID,
    CONF_SCAN,
    CONF_SCL,
    CONF_SDA,
    PLATFORM_ESP32,
)
from esphome.core import CoroPriority, coroutine_with_priority
import esphome.final_validate as fv

LOGGER = logging.getLogger(__name__)
CODEOWNERS = ["@esphome/core"]
MULTI_CONF = True

# Create namespace and classes
i2c_ns = cg.esphome_ns.namespace("i2c")
I2CBus = i2c_ns.class_("I2CBus")
I2CDevice = i2c_ns.class_("I2CDevice")

# For now, we'll use a simple bus class since embhome is Rust-focused
# The actual implementation will be in Rust
EmbhomeI2CBus = i2c_ns.class_("EmbhomeI2CBus", I2CBus, cg.Component)


CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(EmbhomeI2CBus),
            cv.Optional(CONF_SDA, default="SDA"): pins.internal_gpio_pin_number,
            cv.Optional(CONF_SCL, default="SCL"): pins.internal_gpio_pin_number,
            cv.Optional(CONF_FREQUENCY, default="100kHz"): cv.All(
                cv.frequency,
                cv.float_range(min=0, min_included=False),
            ),
            cv.Optional(CONF_SCAN, default=True): cv.boolean,
        }
    ).extend(cv.COMPONENT_SCHEMA),
    cv.only_on([PLATFORM_ESP32]),
)


def _final_validate(config):
    """Validate I2C configuration at the end of config processing."""
    full_config = fv.full_config.get().get(CONF_I2C, [])

    # For now, limit to 2 I2C buses for embhome
    # TODO: Add per-variant limits like ESPHome
    if len(full_config) > 2:
        raise cv.Invalid("The maximum number of I2C interfaces for embhome is 2")


FINAL_VALIDATE_SCHEMA = _final_validate


@coroutine_with_priority(CoroPriority.BUS)
async def to_code(config):
    """Generate code for I2C bus."""
    cg.add_global(i2c_ns.using)
    cg.add_define("USE_I2C")

    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)

    cg.add(var.set_sda_pin(config[CONF_SDA]))
    cg.add(var.set_scl_pin(config[CONF_SCL]))
    cg.add(var.set_frequency(int(config[CONF_FREQUENCY])))
    cg.add(var.set_scan(config[CONF_SCAN]))


def i2c_device_schema(default_address):
    """
    Create a schema for an I2C device.

    Args:
        default_address: The default address of the I2C device, can be None to represent
                        a required option.

    Returns:
        The I2C device schema, extend this in your config schema.
    """
    schema = {
        cv.GenerateID(CONF_I2C_ID): cv.use_id(I2CBus),
    }
    if default_address is None:
        schema[cv.Required(CONF_ADDRESS)] = cv.i2c_address
    else:
        schema[cv.Optional(CONF_ADDRESS, default=default_address)] = cv.i2c_address
    return cv.Schema(schema)


async def register_i2c_device(var, config):
    """
    Register an I2C device with the given config.

    Sets the I2C bus to use and the I2C address.

    This is a coroutine, you need to await it with an 'await' expression!
    """
    parent = await cg.get_variable(config[CONF_I2C_ID])
    cg.add(var.set_i2c_bus(parent))
    cg.add(var.set_i2c_address(config[CONF_ADDRESS]))


def final_validate_device_schema(
    name: str,
    *,
    min_frequency=None,
    max_frequency=None,
):
    """
    Validate device-specific I2C requirements.

    Args:
        name: Component name for error messages
        min_frequency: Minimum required frequency
        max_frequency: Maximum allowed frequency

    Returns:
        Validation schema
    """
    hub_schema = {}

    if (min_frequency is not None) and (max_frequency is not None):
        hub_schema[cv.Required(CONF_FREQUENCY)] = cv.Range(
            min=cv.frequency(min_frequency),
            min_included=True,
            max=cv.frequency(max_frequency),
            max_included=True,
            msg=f"Component {name} requires a frequency between {min_frequency} and {max_frequency} for the I2C bus",
        )
    elif min_frequency is not None:
        hub_schema[cv.Required(CONF_FREQUENCY)] = cv.Range(
            min=cv.frequency(min_frequency),
            min_included=True,
            msg=f"Component {name} requires a minimum frequency of {min_frequency} for the I2C bus",
        )
    elif max_frequency is not None:
        hub_schema[cv.Required(CONF_FREQUENCY)] = cv.Range(
            max=cv.frequency(max_frequency),
            max_included=True,
            msg=f"Component {name} cannot be used with a frequency of over {max_frequency} for the I2C bus",
        )

    return cv.Schema(
        {cv.Required(CONF_I2C_ID): fv.id_declaration_match_schema(hub_schema)},
        extra=cv.ALLOW_EXTRA,
    )
