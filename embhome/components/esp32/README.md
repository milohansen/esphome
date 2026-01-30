# ESP32 Platform Component

Platform support for all ESP32 variants using esp-hal and embassy.

## Python API

```yaml
esp32:
  board: esp32dev              # Board name (optional if variant is set)
  variant: ESP32               # ESP32 variant (optional if board is set)
  cpu_frequency: 160           # CPU frequency in MHz (optional)
  flash_size: 4MB              # Flash size (optional, default: 4MB)
```

**Supported variants:**
- ESP32 (original)
- ESP32-C2, ESP32-C3, ESP32-C5, ESP32-C6, ESP32-C61
- ESP32-H2
- ESP32-P4
- ESP32-S2, ESP32-S3

**Helper functions:**
- `get_variant()` - Returns the ESP32 variant string
- `get_board()` - Returns the board name

## Rust API

```rust
use embhome_esp32::{Platform, PlatformConfig};

// Initialize platform
let config = PlatformConfig {
    cpu_frequency_mhz: 160,
};
Platform::init_global(config);

// Use platform utilities
embhome_esp32::delay_ms(1000);
embhome_esp32::delay_us(500);

let freq = embhome_esp32::get_cpu_frequency_mhz();
```

**Key types:**
- `Platform` - Main platform HAL instance
- `PlatformConfig` - Platform configuration

**Public functions:**
- `Platform::init(config)` - Initialize platform
- `Platform::init_global(config)` - Initialize and store global instance
- `delay_ms(ms)` - Delay for milliseconds
- `delay_us(us)` - Delay for microseconds
- `get_cpu_frequency_mhz()` - Get CPU frequency

## Divergences from ESPHome

**Removed:**
- Framework selection (Arduino/ESP-IDF) - embhome uses esp-hal exclusively
- PlatformIO integration - embhome uses cargo/esp-rs toolchain
- Build system options (sdkconfig, platformio options, etc.)
- Partition table management
- Advanced IDF options (LWIP, VFS, mbedTLS, etc.)
- OTA rollback configuration
- IDF component management

**Simplified:**
- Configuration schema - only essential options (board, variant, cpu_frequency, flash_size)
- No separate framework version management
- No build-time code generation for partition tables
- No custom board definitions (uses esp-hal's board support)

**Added:**
- Direct esp-hal integration
- Simpler configuration model
- Rust-native HAL initialization

## Examples

### Minimal ESP32 config

```yaml
esp32:
  board: esp32dev
```

### ESP32-C3 with custom frequency

```yaml
esp32:
  variant: ESP32C3
  cpu_frequency: 160
```

### ESP32-S3 with larger flash

```yaml
esp32:
  board: esp32-s3-devkitc-1
  flash_size: 8MB
```

### Rust usage

```rust
use embhome_esp32::{Platform, PlatformConfig};

fn main() -> ! {
    // Initialize platform
    let config = PlatformConfig {
        cpu_frequency_mhz: 160,
    };
    Platform::init_global(config);

    loop {
        // Blink LED or other tasks
        embhome_esp32::delay_ms(1000);
    }
}
```
