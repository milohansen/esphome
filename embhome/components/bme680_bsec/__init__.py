"""
Component: bme680_bsec
Status: NOT IMPLEMENTED

Structure:
- Platform types: text_sensor, sensor
- Has platform dirs: False
- Platform subdirs: none

Dependencies: i2c
Auto-load: sensor, text_sensor
Codeowners: @trvrnrth
Core-owned: NO
"""

import esphome.config_validation as cv


def validate_component_not_implemented(config):
    raise cv.Invalid(
        "Component 'bme680_bsec' is not yet implemented in embhome. "
        "This is a stub placeholder."
    )


# Stub schema that raises error
CONFIG_SCHEMA = cv.All(
    cv.Schema({}, extra=cv.ALLOW_EXTRA), validate_component_not_implemented
)


async def to_code(config):
    """This should never be called due to validation error."""
    pass
