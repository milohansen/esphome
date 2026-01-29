"""
Component: daly_bms
Status: NOT IMPLEMENTED

Structure:
- Platform types: text_sensor, sensor, binary_sensor
- Has platform dirs: False
- Platform subdirs: none

Dependencies: uart
Auto-load: none
Codeowners: @s1lvi0
Core-owned: NO
"""

import esphome.config_validation as cv


def validate_component_not_implemented(config):
    raise cv.Invalid(
        "Component 'daly_bms' is not yet implemented in embhome. "
        "This is a stub placeholder."
    )


# Stub schema that raises error
CONFIG_SCHEMA = cv.All(
    cv.Schema({}, extra=cv.ALLOW_EXTRA), validate_component_not_implemented
)


async def to_code(config):
    """This should never be called due to validation error."""
    pass
