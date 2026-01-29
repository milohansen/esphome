"""
Component: hub75
Status: NOT IMPLEMENTED

Structure:
- Platform types: display
- Has platform dirs: True
- Platform subdirs: boards

Dependencies: none
Auto-load: none
Codeowners: @stuartparmenter
Core-owned: NO
"""

import esphome.config_validation as cv


def validate_component_not_implemented(config):
    raise cv.Invalid(
        "Component 'hub75' is not yet implemented in embhome. "
        "This is a stub placeholder."
    )


# Stub schema that raises error
CONFIG_SCHEMA = cv.All(
    cv.Schema({}, extra=cv.ALLOW_EXTRA), validate_component_not_implemented
)


async def to_code(config):
    """This should never be called due to validation error."""
    pass
