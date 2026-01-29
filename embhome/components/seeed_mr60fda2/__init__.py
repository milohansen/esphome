"""
Component: seeed_mr60fda2
Status: NOT IMPLEMENTED

Structure:
- Platform types: binary_sensor
- Has platform dirs: True
- Platform subdirs: select, button

Dependencies: uart
Auto-load: none
Codeowners: @limengdu
Core-owned: NO
"""

import esphome.config_validation as cv


def validate_component_not_implemented(config):
    raise cv.Invalid(
        "Component 'seeed_mr60fda2' is not yet implemented in embhome. "
        "This is a stub placeholder."
    )


# Stub schema that raises error
CONFIG_SCHEMA = cv.All(
    cv.Schema({}, extra=cv.ALLOW_EXTRA), validate_component_not_implemented
)


async def to_code(config):
    """This should never be called due to validation error."""
    pass
