"""
Component: bl0940
Status: NOT IMPLEMENTED

Structure:
- Platform types: sensor
- Has platform dirs: True
- Platform subdirs: button, number

Dependencies: none
Auto-load: none
Codeowners: @tobias-, @dan-s-github
Core-owned: NO
"""

import esphome.config_validation as cv


def validate_component_not_implemented(config):
    raise cv.Invalid(
        "Component 'bl0940' is not yet implemented in embhome. "
        "This is a stub placeholder."
    )


# Stub schema that raises error
CONFIG_SCHEMA = cv.All(
    cv.Schema({}, extra=cv.ALLOW_EXTRA), validate_component_not_implemented
)


async def to_code(config):
    """This should never be called due to validation error."""
    pass
