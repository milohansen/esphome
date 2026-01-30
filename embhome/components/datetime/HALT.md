# HALT: Partial Implementation of Datetime Component

## Reason for Halt
While the core functionality of the `datetime` component is implemented and the configuration schema matches the ESPHome base reference, certain high-level features are not yet available or integrated.

## Specific Blocker(s)
1. **MQTT and Web Server Integration**
   - **Issue**: These features are not yet defined for this component in the Rust environment.
   - **Status**: Removed from configuration to avoid confusion until they are supported.
2. **Internal Automation Triggers (`on_value`, `on_time`)**
   - **Issue**: The current actor pattern delegates automation to external listeners of `DatetimeEvent` rather than executing actions internally.
   - **Status**: Configuration options are recognized for schema compatibility.

## What I've Completed
- [x] Ported all C++ validation logic.
- [x] Matched the base ESPHome configuration schema in Rust (removed `type`, `mqtt_id`, and `web_server` per feedback).
- [x] Established the Actor pattern and message protocol.

## Recommended Next Steps
- Integration with a global MQTT actor once the pattern is established.
- Implementation of a generic Web Server component that can query `DatetimeActor`.
- Development of a unified Automation Engine that can consume `DatetimeEvent`.
