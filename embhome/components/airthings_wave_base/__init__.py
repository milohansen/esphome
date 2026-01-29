"""
Component: airthings_wave_base
Status: NOT IMPLEMENTED

Structure:
- Platform types: component
- Has platform dirs: False
- Platform subdirs: none

Dependencies: ble_client
Auto-load: none
Codeowners: @ncareau, @jeromelaban, @kpfleming
Core-owned: NO
"""

import esphome.config_validation as cv


def validate_component_not_implemented(config):
    raise cv.Invalid(
        "Component 'airthings_wave_base' is not yet implemented in embhome. "
        "This is a stub placeholder."
    )


# Stub schema that raises error
CONFIG_SCHEMA = cv.All(
    cv.Schema({}, extra=cv.ALLOW_EXTRA), validate_component_not_implemented
)


async def to_code(config):
    """This should never be called due to validation error."""
    pass
