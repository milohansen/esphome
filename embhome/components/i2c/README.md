# I2C Component

## Python API

```yaml
i2c:
  id: bus_a                    # Optional
  sda: 21                      # Default: SDA
  scl: 22                      # Default: SCL
  frequency: 100kHz            # Default: 100kHz
  scan: true                   # Default: true

# Helper for I2C devices
sensor:
  - platform: some_i2c_sensor
    i2c_id: bus_a              # Optional, uses default bus
    address: 0x76              # Device address
```

**Helper functions:**
- `i2c_device_schema(address)` - Creates schema for I2C devices
- `register_i2c_device(var, config)` - Registers device with bus
- `final_validate_device_schema(name, min_frequency, max_frequency)` - Validates device requirements

## Rust API

```rust
use esphome_i2c::{I2CBus, I2CDevice};

// Initialize bus
let mut bus = I2CBus::new(
    peripherals.I2C0,
    io.pins.gpio21,  // SDA
    io.pins.gpio22,  // SCL
    100_000,         // Frequency in Hz
);

// Scan for devices
let devices = bus.scan();

// Create device wrapper
let mut sensor = I2CDevice::new(&mut bus, 0x76);

// Read/write operations
sensor.read(&mut buffer)?;
sensor.write(&data)?;
sensor.write_read(&write_data, &mut read_buffer)?;

// Register access
let value = sensor.read_register_byte(0x00)?;
sensor.write_register_byte(0x01, 0xA0)?;
let temp = sensor.read_register_u16(0x22)?;

// Bit manipulation
sensor.set_bits(0x02, 0x08)?;
sensor.clear_bits(0x02, 0x80)?;
sensor.modify_register(0x02, |v| (v & 0xF0) | 0x05)?;
```

## Divergences from ESPHome

**Removed:**
- Timeout configuration (can add if needed)
- Pullup enable/disable (can add if needed)
- Low-power mode (ESP32-specific, can add later)
- ESP8266, RP2040, Zephyr support (ESP32 only for now)

**Simplified:**
- Max 2 buses (vs per-variant limits)

**Added (Rust):**
- `I2CDevice` wrapper for cleaner device code
- Bit manipulation helpers (`set_bits`, `clear_bits`, `modify_register`)
- 16-bit register support
- embedded-hal trait implementation
- Type-safe error handling

## Example

```yaml
esphome:
  name: i2c-test
  platform: ESP32

i2c:
  sda: 21
  scl: 22
  frequency: 100kHz
  scan: true
```

```rust
// Device implementation example
pub struct Bme280<'a, 'd> {
    device: I2CDevice<'a, 'd>,
}

impl<'a, 'd> Bme280<'a, 'd> {
    pub fn new(bus: &'a mut I2CBus<'d>) -> Result<Self, Error> {
        let mut device = I2CDevice::new(bus, 0x76);
        let chip_id = device.read_register_byte(0xD0)?;
        if chip_id != 0x60 {
            return Err(Error::Other);
        }
        Ok(Self { device })
    }

    pub fn read_temperature(&mut self) -> Result<f32, Error> {
        let mut data = [0u8; 3];
        self.device.read_register(0xFA, &mut data)?;
        let raw = ((data[0] as u32) << 12) | ((data[1] as u32) << 4) | ((data[2] as u32) >> 4);
        Ok(raw as f32 / 100.0)
    }
}
```
