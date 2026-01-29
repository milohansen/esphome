# Example Generated ESPHome Project

This directory shows what the Python code generator would create for a device.

## Project Structure

```
living-room-sensor/
├── Cargo.toml          # Generated with correct chip features
├── .cargo/
│   └── config.toml     # Target and runner configuration
├── src/
│   └── main.rs         # Generated main function with component tasks
└── config.yaml         # Original ESPHome YAML (for reference)
```

## Key Features

### 1. Chip Feature Propagation

All dependencies include `features = ["esp32c3"]`:

```toml
esphome-wifi = { path = "../components/wifi", features = ["esp32c3"] }
```

This ensures:
- `esp-hal` compiles for ESP32-C3
- `esp-wifi` uses ESP32-C3 WiFi driver
- All components know the target chip

### 2. Version Consistency

All versions match the workspace:

```toml
embassy-executor = { version = "0.9.1", features = ["executor-thread"] }
```

No duplicates possible!

### 3. Default Feature

The chip feature is default, so it's always enabled:

```toml
[features]
default = ["esp32c3"]
```

## Building

```bash
# Build
cargo build --release

# Flash to device
cargo run --release

# Or use espflash directly
espflash flash target/riscv32imc-unknown-none-elf/release/living-room-sensor
```

## How It's Generated

The Python code generator:

1. Reads YAML configuration
2. Determines required components
3. Detects chip from `platform: esp32c3`
4. Uses `codegen_helpers.py` to generate Cargo.toml with correct features
5. Generates main.rs with component initialization
6. Generates .cargo/config.toml for the target

## Example YAML

```yaml
esphome:
  name: living-room-sensor
  platform: esp32c3

wifi:
  ssid: "MyNetwork"
  password: "secret"

api:
  encryption:
    key: "base64key=="

sensor:
  - platform: uptime
    name: "Uptime"

binary_sensor:
  - platform: gpio
    name: "Button"
    pin: GPIO9
```

Would generate this project structure with all necessary dependencies and features.
