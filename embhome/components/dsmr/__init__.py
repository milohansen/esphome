"""
Component: dsmr
Status: NOT IMPLEMENTED

Structure:
- Platform types: text_sensor, sensor
- Has platform dirs: False
- Platform subdirs: none

Dependencies: uart
Auto-load: sensor, text_sensor
Codeowners: @glmnet, @zuidwijk, @PolarGoose
Core-owned: NO
"""

import esphome.config_validation as cv


def validate_component_not_implemented(config):
    raise cv.Invalid(
        "Component 'dsmr' is not yet implemented in embhome. "
        "This is a stub placeholder."
    )


# Stub schema that raises error
CONFIG_SCHEMA = cv.All(
    cv.Schema({}, extra=cv.ALLOW_EXTRA), validate_component_not_implemented
)


async def to_code(config):
    """This should never be called due to validation error."""
    pass
