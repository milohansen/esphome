# Implementation Summary: datetime

## What Was Implemented
- **Actor Pattern**: Fully implemented `DatetimeActor` with message-based control.
- **Entity Types**: Support for `DATE`, `TIME`, and `DATETIME` via `DatetimeType` configuration.
- **Validation**: Ported all date/time validation logic from ESPHome C++:
    - Leap year detection.
    - Days in month validation.
    - Range checks for year (1970-3000), month, hour, minute, second.
- **Message Protocol**: Comprehensive `DatetimeMessage` and `DatetimeEvent` enums.
- **State Persistence**: `DatetimeState` struct tracking all fields and last update timestamp.

## What Was Changed
- **Async First**: All interactions are async and follow the `embassy` pattern.
- **Flat Structure**: Instead of a class hierarchy (C++), a single Actor handles all types based on configuration, which is more idiomatic for Rust actors.
- **No Direct RTC Link**: In this initial version, the link to an RTC is handled via the system-level orchestration (receiving messages) rather than a direct pointer, ensuring better isolation.

## What Was Not Implemented
- **Web Server / MQTT Integration**: These are handled by separate high-level components in the Rust ecosystem.
- **Restore State**: Persistence logic is delegated to the core system's preference management.

## Testing Recommendations
- Verify that setting invalid dates (e.g., Feb 29 on non-leap years) returns an `Error` event.
- Verify that `Date` only entities reject `SetTime` messages with a `ConfigError`.
- Verify that `StateChanged` events contain the correct updated fields.

## ESPHome Equivalence
| ESPHome Feature | Rust Implementation | Notes |
|-----------------|---------------------|-------|
| `DateEntity`    | `DatetimeActor` (Date) | Same validation logic |
| `TimeEntity`    | `DatetimeActor` (Time) | Same validation logic |
| `DateTimeEntity`| `DatetimeActor` (Datetime) | Same validation logic |
| `control()`     | `handle_message()` | Async message processing |
| `publish_state()`| `event_tx.send()`  | Event-driven state updates |

## Known Limitations
- Does not yet automatically sync with an RTC; depends on an external actor to send `Set*` messages if synchronization is needed.
