# Component Design: datetime

## File Structure
```
datetime/
├── Cargo.toml
├── README.md
├── ANALYSIS.md
├── src/
│   ├── lib.rs          # Public API and types
│   ├── actor.rs        # Actor implementation
│   ├── config.rs       # Configuration types
│   ├── messages.rs     # Message and Event enums
│   └── error.rs        # Error types
└── examples/
    └── basic_usage.rs
```

## Configuration Schema (Rust)
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatetimeConfig {
    pub id: Option<String>,
    pub name: String,
    pub type_: DatetimeType,
    pub update_interval: Option<u64>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum DatetimeType {
    Date,
    Time,
    DateTime,
}
```

## Message Protocol
```rust
pub enum DatetimeMessage {
    SetDate(u16, u8, u8),           // Year, Month, Day
    SetTime(u8, u8, u8),           // Hour, Minute, Second
    SetDateTime(u16, u8, u8, u8, u8, u8),
    GetState(Sender<'static, Result<DatetimeState, DatetimeError>, 1>),
    Shutdown,
}

pub enum DatetimeEvent {
    Ready,
    StateChanged(DatetimeState),
    Error(DatetimeError),
}

#[derive(Debug, Clone, Copy, Default)]
pub struct DatetimeState {
    pub year: Option<u16>,
    pub month: Option<u8>,
    pub day: Option<u8>,
    pub hour: Option<u8>,
    pub minute: Option<u8>,
    pub second: Option<u8>,
}
```

## State Machine
```
[Created] -> [Initializing] -> [Ready] -> [Shutdown]
```

## Resource Requirements
- I2C device: No
- GPIO pins: No
- Memory: Minimal (~1KB stack)
- Channel sizes: Message: 16, Event: 16

## Implementation Notes
- The actor will maintain the current state and validate any incoming `Set*` messages.
- If an RTC is linked (in future expansion), it would synchronize with it.
- Validation logic from C++ will be ported:
    - Year: 1970-3000
    - Month: 1-12
    - Day: 1-31 (validated against month/year)
    - Hour: 0-23
    - Minute: 0-59
    - Second: 0-59
