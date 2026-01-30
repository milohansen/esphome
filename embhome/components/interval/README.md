# Interval Component

The `interval` component allows you to run actions at fixed time intervals. It uses the Embassy async runtime to provide efficient, non-blocking periodic triggers.

## Python API

```yaml
interval:
  - interval: 1min
    startup_delay: 0s
    then:
      - logger.log: "Triggered!"
```

*Note: In the current Rust implementation, the `then` actions are not yet fully integrated with the Rust-based automation system.*

## Rust API

```rust
use esphome_interval::{IntervalActor, IntervalConfig};

// Create a new interval actor
let mut actor = IntervalActor::new("my_interval");

// Configure with 1 second interval and no startup delay
let config = IntervalConfig {
    interval_ms: 1000,
    startup_delay_ms: 0,
};

// Setup and run (within an async context)
actor.setup(config).await?;
actor.run(mailbox_receiver).await;
```

### Messages

- `IntervalMessage::SetInterval(Duration)`: Change the interval at runtime.

### Events

- `IntervalEvent::Ready`: Emitted after the startup delay has passed.
- `IntervalEvent::Triggered`: Emitted every time the interval expires.

## Divergences from ESPHome

**Simplified:**
- Uses Embassy `Timer` and `Instant` for timing instead of ESPHome's `PollingComponent` clock.
- Logic is implemented as an asynchronous Actor task.

## Example

```yaml
interval:
  - interval: 5s
    startup_delay: 2s
```
