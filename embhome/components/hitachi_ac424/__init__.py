"""
Component: hitachi_ac424
Status: NOT IMPLEMENTED

Structure:
- Platform types: climate
- Has platform dirs: False
- Platform subdirs: none

Dependencies: none
Auto-load: none
Codeowners: @sourabhjaiswal
Core-owned: NO
"""

import esphome.config_validation as cv


def validate_component_not_implemented(config):
    raise cv.Invalid(
        "Component 'hitachi_ac424' is not yet implemented in embhome. "
        "This is a stub placeholder."
    )


# Stub schema that raises error
CONFIG_SCHEMA = cv.All(
    cv.Schema({}, extra=cv.ALLOW_EXTRA), validate_component_not_implemented
)


async def to_code(config):
    """This should never be called due to validation error."""
    pass
