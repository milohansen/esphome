# Datetime Component

Actor-based component for managing date and time entities in the ESPHome-style modular Rust firmware.

## Features

- ✅ Support for Date, Time, and DateTime entity types.
- ✅ Validation of input values (leap years, month days, etc.).
- ✅ Message-passing interface for setting and getting state.
- ✅ Event-driven notifications for state changes.
- ✅ Generic and self-contained (no hardware dependencies).
- ✅ Compatible with ESPHome configuration schema.

## YAML Configuration

```yaml
datetime:
  - platform: template
    name: "Target Date"
    id: my_date
    icon: "mdi:calendar"
    type: DATE
    time_id: my_rtc         # Optional link to RTC
    mqtt_id: my_mqtt       # Recognized but not yet implemented
    web_server: true       # Recognized but not yet implemented
    on_value:              # Handled via DatetimeEvent::StateChanged
      then:
        - ...
    on_time:               # Handled by external timer actors
      - seconds: 0
        minutes: 30
        hours: 10
        then:
          - ...
```

## Messages

### Received
- `SetDate { year, month, day }`: Update date (for Date/DateTime types).
- `SetTime { hour, minute, second }`: Update time (for Time/DateTime types).
- `SetDateTime { ... }`: Update both (for DateTime type).
- `GetState(response)`: Request current state.
- `Shutdown`: Graceful shutdown.

### Sent
- `Ready`: Component initialized and ready.
- `StateChanged(state)`: Emitted when state is successfully updated.
- `Error(error)`: Emitted on validation or configuration errors.
- `ShutdownComplete`: Shutdown finished.

## Resource Requirements

- 16-slot message channel (recommended).
- 16-slot event channel (recommended).
- ~1KB stack space.

## Example Usage

See `examples/basic_usage.rs` for a complete example.
