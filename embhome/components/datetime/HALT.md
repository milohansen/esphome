# HALT: Partial Implementation of Datetime Component

## Reason for Halt
While the core functionality of the `datetime` component is implemented and the configuration schema matches the ESPHome reference, certain high-level features are not yet functional in the Rust actor.

## Specific Blocker(s)
1. **MQTT Integration (`mqtt_id`)**
   - **Issue**: The Rust actor ecosystem for MQTT is not yet unified with individual component actors.
   - **Status**: Configuration option is supported but the actor only logs a warning.
2. **Web Server Integration (`web_server`)**
   - **Issue**: No standard async web server interface is currently available for this component in the Rust environment.
   - **Status**: Configuration option is supported but the actor only logs a warning.
3. **Internal Automation Triggers (`on_value`, `on_time`)**
   - **Issue**: The current actor pattern delegates automation to external listeners of `DatetimeEvent` rather than executing actions internally.
   - **Status**: Configuration options are recognized for schema compatibility.

## What I've Completed
- [x] Ported all C++ validation logic.
- [x] Implemented Date, Time, and DateTime entity modes.
- [x] Matched the original ESPHome configuration schema in Rust.
- [x] Established the Actor pattern and message protocol.

## Recommended Next Steps
- Integration with a global MQTT actor.
- Implementation of a generic Web Server component that can query `DatetimeActor`.
- Development of a unified Automation Engine that can consume `DatetimeEvent`.
