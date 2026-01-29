"""
Component: sm2135
Status: NOT IMPLEMENTED

Structure:
- Platform types: output
- Has platform dirs: False
- Platform subdirs: none

Dependencies: none
Auto-load: output
Codeowners: @BoukeHaarsma23, @matika77, @dd32
Core-owned: NO
"""

import esphome.config_validation as cv


def validate_component_not_implemented(config):
    raise cv.Invalid(
        "Component 'sm2135' is not yet implemented in embhome. "
        "This is a stub placeholder."
    )


# Stub schema that raises error
CONFIG_SCHEMA = cv.All(
    cv.Schema({}, extra=cv.ALLOW_EXTRA), validate_component_not_implemented
)


async def to_code(config):
    """This should never be called due to validation error."""
    pass
