# Component Design

## File Structure
```
interval/
├── Cargo.toml
├── README.md
├── src/
│   ├── lib.rs
│   ├── actor.rs
│   ├── config.rs
│   ├── messages.rs
│   ├── error.rs
└── examples/
    └── basic_usage.rs
```

## Configuration Schema (Rust)
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IntervalConfig {
    pub interval: Duration,
    pub startup_delay: Duration,
}
```

## Message Protocol
```rust
pub enum IntervalMessage {
    SetInterval(Duration),
}

pub enum IntervalEvent {
    Ready,
    Triggered,
}
```

## State Machine
```
Created -> Initializing (waiting for startup_delay) -> Ready -> Running (waiting for interval) -> Triggering -> Running
```

## Resource Requirements
- I2C device: No
- GPIO pins: No
- Memory: Minimal (Actor state + message channels)
- Channel sizes: Message: 8, Event: 8

## Implementation Notes
- The actor will use `embassy_time::Timer` for both the startup delay and the periodic interval.
- `select` will be used to handle both incoming messages (e.g., to change the interval) and the timer.
