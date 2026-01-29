# UART Component

## Python API

```yaml
uart:
  id: uart_bus                 # Optional
  tx_pin: 17                   # Optional (at least one required)
  rx_pin: 16                   # Optional (at least one required)
  baud_rate: 115200            # Required
  data_bits: 8                 # Default: 8 (5-8)
  stop_bits: 1                 # Default: 1 (1-2)
  parity: NONE                 # Default: NONE (NONE/EVEN/ODD)
  rx_buffer_size: 256          # Default: 256 bytes
```

**Helper functions:**
- `UART_DEVICE_SCHEMA` - Schema for UART devices
- `register_uart_device(var, config)` - Registers device with UART bus
- `final_validate_device_schema(name, baud_rate, require_tx, require_rx)` - Validates device requirements

## Rust API

```rust
use esphome_uart::{UARTComponent, UARTDevice};

// Initialize UART
let mut uart = UARTComponent::new(
    peripherals.UART0,
    io.pins.gpio17,  // TX
    io.pins.gpio16,  // RX
    115200,          // Baud rate
);

// TX or RX only
let mut uart_tx = UARTComponent::new_tx_only(peripherals.UART1, tx_pin, 9600);
let mut uart_rx = UARTComponent::new_rx_only(peripherals.UART2, rx_pin, 9600);

// Write operations
uart.write_byte(0x42)?;
uart.write_bytes(&[1, 2, 3])?;
uart.flush()?;

// Read operations
let byte = uart.read_byte()?;
let count = uart.read_bytes(&mut buffer)?;
let available = uart.available();

// Device wrapper
let mut device = UARTDevice::new(&mut uart);
device.write_str("Hello\n")?;
let line_len = device.read_line(&mut buffer)?;
let count = device.read_until(b'\r', &mut buffer)?;

// embedded-io traits
use embedded_io::{Read, Write};
uart.write(b"data")?;
uart.read(&mut buffer)?;
```

## Divergences from ESPHome

**Removed:**
- Debug mode (can add if needed)
- Flow control pin (can add if needed)
- Hardware-specific optimizations (ESP8266 Serial, ESP32 RX threshold)
- UART write actions/automation
- Host platform support

**Simplified:**
- ESP32 only (for now)
- Basic configuration (no advanced ESP32-specific tuning)
- No automatic port selection based on pins

**Added (Rust):**
- `UARTDevice` wrapper for cleaner device code
- `read_until()` and `read_line()` helpers
- TX-only and RX-only modes
- embedded-io trait implementation

## Example

```yaml
esphome:
  name: uart-test
  platform: ESP32

uart:
  - id: uart1
    tx_pin: 17
    rx_pin: 16
    baud_rate: 9600

  - id: uart2
    tx_pin: 4
    rx_pin: 5
    baud_rate: 115200
    parity: EVEN
```

```rust
// GPS device example
pub struct GPSDevice<'a, 'd> {
    uart: UARTDevice<'a, 'd>,
}

impl<'a, 'd> GPSDevice<'a, 'd> {
    pub fn new(uart_bus: &'a mut UARTComponent<'d>) -> Self {
        Self {
            uart: UARTDevice::new(uart_bus),
        }
    }

    pub fn read_nmea_sentence(&mut self, buffer: &mut [u8]) -> Result<usize, Error> {
        // Read until newline
        self.uart.read_line(buffer)
    }
}
```
