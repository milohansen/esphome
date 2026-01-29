"""
Component: espnow
Status: NOT IMPLEMENTED

Structure:
- Platform types: component
- Has platform dirs: True
- Platform subdirs: packet_transport

Dependencies: none
Auto-load: socket
Codeowners: @jesserockz
Core-owned: NO
"""

import esphome.config_validation as cv


def validate_component_not_implemented(config):
    raise cv.Invalid(
        "Component 'espnow' is not yet implemented in embhome. "
        "This is a stub placeholder."
    )


# Stub schema that raises error
CONFIG_SCHEMA = cv.All(
    cv.Schema({}, extra=cv.ALLOW_EXTRA), validate_component_not_implemented
)


async def to_code(config):
    """This should never be called due to validation error."""
    pass
