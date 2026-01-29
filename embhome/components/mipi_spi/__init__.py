"""
Component: mipi_spi
Status: NOT IMPLEMENTED

Structure:
- Platform types: display
- Has platform dirs: True
- Platform subdirs: models

Dependencies: none
Auto-load: none
Codeowners: @clydebarrow
Core-owned: NO
"""

import esphome.config_validation as cv


def validate_component_not_implemented(config):
    raise cv.Invalid(
        "Component 'mipi_spi' is not yet implemented in embhome. "
        "This is a stub placeholder."
    )


# Stub schema that raises error
CONFIG_SCHEMA = cv.All(
    cv.Schema({}, extra=cv.ALLOW_EXTRA), validate_component_not_implemented
)


async def to_code(config):
    """This should never be called due to validation error."""
    pass
