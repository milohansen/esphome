# Component Analysis

## Component Type
[x] High-Level (sensor, protocol handler, etc.)
[ ] Mid-Level (bus manager, shared resource)
[ ] Low-Level (hardware abstraction, DMA controller)

Reasoning: The interval component is a software-based trigger that doesn't interact directly with hardware peripherals. It uses the system timer to trigger actions at fixed intervals, making it a high-level orchestration component.

## Hardware Requirements
- Communication protocol: None
- I2C address (if applicable): N/A
- Pin requirements: None
- Power requirements: N/A
- Timing constraints: Uses system timer. Accuracy depends on the underlying RTOS/executor (Embassy timer).

## Configuration Schema (from Python)
```yaml
interval:
  - interval: 1min  # Required
    startup_delay: 0s # Optional, default 0s
    then:           # Required
      - switch.toggle: relay_1
```

## Core Functionality (from C++)
1. Initialization sequence:
    - Set the update interval.
    - Set the startup delay.
    - In `setup()`, if `startup_delay` is non-zero, stop the poller and set a timeout to start it after the delay.
2. Main operations:
    - The `update()` method (called by the poller every `interval`) calls `trigger()`.
3. Data structures:
    - `startup_delay_`: Stores the initial delay.
4. Hardware interactions:
    - None. Uses `PollingComponent`'s built-in timer mechanism.
5. Error conditions:
    - None defined in the reference.

## Message Protocol Design

### Messages (what this component receives):
- `Initialize(config)`: Sets the interval and startup delay.
- `UpdateConfig(new_interval)`: Optionally allows changing the interval at runtime.

### Events (what this component sends):
- `Ready`: Sent when the component is fully initialized (after startup delay).
- `Triggered`: Sent every time the interval expires.
- `Error(error)`: If any unexpected error occurs (unlikely for this component).

## Dependencies Identified
- `embassy-sync`: For channels and mutexes.
- `embassy-time`: For timers and durations.
- `esphome-core`: For the `Component` trait and base types.
- `serde`: For configuration deserialization.
- `log`: For logging.

## Calibration/Compensation
- Does this component need calibration data? No.

## Open Questions
1. Should `interval` be a separate component in Rust or just a helper?
   - Impact: If it's a component, it follows the actor pattern.
   - Current assumption: It will be a full component to stay consistent with the "Actor Pattern" requirement.
2. How to handle the `then` actions in Rust?
   - Impact: In ESPHome, actions are compiled to C++ code. In Rust, we might send an event that an automation component listens to.
   - Current assumption: We will send an `IntervalEvent::Triggered` message to any subscribers.
