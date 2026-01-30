"""ESP32 Platform Component for embhome

This component provides ESP32 platform support using esp-hal and embassy.
Supports all ESP32 variants (ESP32, C2, C3, C5, C6, C61, H2, P4, S2, S3).
"""

from dataclasses import dataclass

import esphome.codegen as cg
from esphome.components.esp32.boards import BOARDS, STANDARD_BOARDS

# Import constants from ESPHome
from esphome.components.esp32.const import (
    VARIANT_ESP32,
    VARIANT_ESP32C2,
    VARIANT_ESP32C3,
    VARIANT_ESP32C5,
    VARIANT_ESP32C6,
    VARIANT_ESP32C61,
    VARIANT_ESP32H2,
    VARIANT_ESP32P4,
    VARIANT_ESP32S2,
    VARIANT_ESP32S3,
    VARIANT_FRIENDLY,
    VARIANTS,
)
import esphome.config_validation as cv
from esphome.const import (
    CONF_BOARD,
    CONF_VARIANT,
    KEY_CORE,
    KEY_TARGET_PLATFORM,
    PLATFORM_ESP32,
)
from esphome.core import CORE

AUTO_LOAD = ["preferences"]
CODEOWNERS = ["@esphome/core"]
IS_TARGET_PLATFORM = True

DOMAIN = "esp32"

CONF_CPU_FREQUENCY = "cpu_frequency"
CONF_FLASH_SIZE = "flash_size"

# CPU frequencies for each variant (in MHz)
CPU_FREQUENCIES = {
    VARIANT_ESP32: [80, 160, 240],
    VARIANT_ESP32C2: [80, 120],
    VARIANT_ESP32C3: [80, 160],
    VARIANT_ESP32C5: [80, 160, 240],
    VARIANT_ESP32C6: [80, 120, 160],
    VARIANT_ESP32C61: [80, 120, 160],
    VARIANT_ESP32H2: [16, 32, 48, 64, 96],
    VARIANT_ESP32P4: [40, 360, 400],
    VARIANT_ESP32S2: [80, 160, 240],
    VARIANT_ESP32S3: [80, 160, 240],
}

FLASH_SIZES = ["2MB", "4MB", "8MB", "16MB", "32MB"]


@dataclass
class Esp32Data:
    """Platform data stored in CORE.data"""

    board: str
    variant: str
    cpu_frequency: int
    flash_size: str


def _get_data() -> Esp32Data:
    """Get ESP32 platform data from CORE.data"""
    if DOMAIN not in CORE.data:
        raise ValueError("ESP32 platform not configured")
    return CORE.data[DOMAIN]


def get_variant() -> str:
    """Get the ESP32 variant (e.g., ESP32, ESP32C3, ESP32S3)"""
    return _get_data().variant


def get_board() -> str:
    """Get the board name"""
    return _get_data().board


def _detect_variant(config):
    """Detect variant from board or validate variant matches board"""
    board = config.get(CONF_BOARD)
    variant = config.get(CONF_VARIANT)

    if variant and board is None:
        # Derive board from variant
        config = config.copy()
        config[CONF_BOARD] = STANDARD_BOARDS[variant]
    elif board in BOARDS:
        # Validate variant matches board
        board_variant = BOARDS[board]["variant"]
        if variant and variant != board_variant:
            raise cv.Invalid(
                f"Option '{CONF_VARIANT}' does not match selected board.",
                path=[CONF_VARIANT],
            )
        config = config.copy()
        config[CONF_VARIANT] = board_variant
    elif not variant:
        raise cv.Invalid(
            "This board is unknown, if you are sure you want to compile with this board selection, "
            f"override with option '{CONF_VARIANT}'",
            path=[CONF_BOARD],
        )

    return config


def _set_cpu_frequency(config):
    """Set default CPU frequency if not specified"""
    config = config.copy()
    variant = config[CONF_VARIANT]
    cpu_frequency = config.get(CONF_CPU_FREQUENCY)

    if cpu_frequency is None:
        # Default to 160MHz if supported, otherwise the fastest
        choices = CPU_FREQUENCIES[variant]
        if 160 in choices:
            cpu_frequency = 160
        elif 360 in choices:
            cpu_frequency = 360
        else:
            cpu_frequency = choices[-1]
        config[CONF_CPU_FREQUENCY] = cpu_frequency
    elif cpu_frequency not in CPU_FREQUENCIES[variant]:
        raise cv.Invalid(
            f"Invalid CPU frequency '{cpu_frequency}MHz' for {config[CONF_VARIANT]}. "
            f"Valid frequencies: {CPU_FREQUENCIES[variant]}",
            path=[CONF_CPU_FREQUENCY],
        )

    return config


def _store_platform_data(config):
    """Store ESP32 platform data in CORE.data"""
    CORE.data[DOMAIN] = Esp32Data(
        board=config[CONF_BOARD],
        variant=config[CONF_VARIANT],
        cpu_frequency=config[CONF_CPU_FREQUENCY],
        flash_size=config[CONF_FLASH_SIZE],
    )
    CORE.data[KEY_CORE][KEY_TARGET_PLATFORM] = PLATFORM_ESP32
    return config


CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.Optional(CONF_BOARD): cv.string_strict,
            cv.Optional(CONF_VARIANT): cv.one_of(*VARIANTS, upper=True),
            cv.Optional(CONF_CPU_FREQUENCY): cv.int_,
            cv.Optional(CONF_FLASH_SIZE, default="4MB"): cv.one_of(
                *FLASH_SIZES, upper=True
            ),
        }
    ),
    _detect_variant,
    _set_cpu_frequency,
    _store_platform_data,
    cv.has_at_least_one_key(CONF_BOARD, CONF_VARIANT),
)


async def to_code(config):
    """Generate Rust code for ESP32 platform"""
    data = _get_data()
    _ = config  # Config already processed and stored in CORE.data

    # Add platform defines
    cg.add_define("USE_ESP32")
    cg.add_define("ESPHOME_BOARD", data.board)
    cg.add_define(f"USE_ESP32_VARIANT_{data.variant}")
    cg.add_define("ESPHOME_VARIANT", VARIANT_FRIENDLY[data.variant])

    # Add build flags for Rust compilation
    variant_lower = data.variant.lower().replace("esp32", "esp32-")
    if data.variant == VARIANT_ESP32:
        variant_lower = "esp32"

    # Store target for cargo build
    cg.add_define("ESP32_TARGET", variant_lower)
    cg.add_define("ESP32_CPU_FREQ_MHZ", data.cpu_frequency)
    cg.add_define("ESP32_FLASH_SIZE", data.flash_size)
