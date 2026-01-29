# Quick Reference: Component Types and Examples

## Component Structure Types

### 1. Base Platform Types (Core-owned)
These define the fundamental entity types in ESPHome:

| Component | Type | Dependents | Purpose |
|-----------|------|------------|---------|
| sensor | Base | 1 | Temperature, humidity, voltage, etc. |
| binary_sensor | Base | 0 | Motion, door, window, occupancy |
| switch | Base | 0 | Relays, GPIO toggles |
| light | Base | 0 | RGB, dimmer, single color |
| climate | Base | 0 | Thermostats, HVAC |
| cover | Base | 0 | Blinds, curtains, garage doors |
| fan | Base | 0 | Fan speed control |
| lock | Base | 0 | Smart locks |
| button | Base | 0 | Momentary actions |
| number | Base | 0 | Numeric input |
| select | Base | 0 | Dropdown selection |

### 2. Communication Protocols (Core-owned)
Critical infrastructure for device communication:

| Component | Dependents | Purpose |
|-----------|------------|---------|
| i2c | 51 | I²C bus communication |
| uart | 30 | Serial UART communication |
| spi | 19 | SPI bus communication |
| network | 10 | Network stack base |

### 3. Platform Components
Target hardware platforms:

| Component | Dependents | Status |
|-----------|------------|--------|
| esp32 | 13 | Core platform |
| esp8266 | 0 | Core platform |
| rp2040 | 1 | Secondary platform |
| libretiny | 0 | Secondary platform |

### 4. Infrastructure (Core-owned)
System-level services:

| Component | Dependencies | Purpose |
|-----------|--------------|---------|
| api | network | Native ESPHome API |
| logger | - | System logging |
| ota | - | Over-the-air updates |
| mdns | network | mDNS discovery |
| web_server_base | network | Web server foundation |

## Example Component Stubs

### Simple Sensor (adc)
```python
"""
Component: adc
Status: NOT IMPLEMENTED

Structure:
- Platform types: sensor
Dependencies: none
Codeowners: @esphome/core
Core-owned: YES
"""
```

### Protocol with Many Dependents (i2c)
```python
"""
Component: i2c
Status: NOT IMPLEMENTED

Structure:
- Platform types: component
Dependencies: none
Codeowners: @esphome/core
Core-owned: YES
[51 other components depend on this]
"""
```

### Component with Platform Subdirs (gpio)
```python
"""
Component: gpio
Status: NOT IMPLEMENTED

Structure:
- Platform types: component
- Has platform dirs: True
- Platform subdirs: switch, binary_sensor, one_wire, output
Dependencies: none
Codeowners: @esphome/core
Core-owned: YES
"""
```

### Complex Component with Dependencies (api)
```python
"""
Component: api
Status: NOT IMPLEMENTED

Structure:
- Platform types: component
Dependencies: network
Codeowners: @esphome/core
Core-owned: YES
"""
```

### Device Driver (bme280)
```python
"""
Component: bme280
Status: NOT IMPLEMENTED

Structure:
- Platform types: sensor
Dependencies: bme280_base, i2c
Codeowners: @esphome/core
Core-owned: NO
"""
```

## Implementation Strategy

### Start Here (Phase 1 - 11 components)
Focus on the critical path that enables the most other components:

```
i2c → esp32 → uart → esp8266 → spi → sensor → binary_sensor → network → switch → api → logger
```

### Then Build Infrastructure (Phase 2 - 3 components)
```
mdns → ota → web_server_base
```

### Add Core Utilities (Phase 3 - 20 components)
```
adc, gpio, output, globals, script, interval, preferences, etc.
```

### Platform Extensions (Phase 4 - 16 components)
```
Additional platforms (rp2040, etc.) and platform types (fan, text_sensor, etc.)
```

## Dependency Chain Examples

### Example 1: BME280 Temperature Sensor
```
bme280 → bme280_base (helper)
      → i2c (protocol)
      → sensor (base type)
```

### Example 2: Web Dashboard
```
web_server → web_server_base → network
                             → api → network
                             → mdns → network
```

### Example 3: UART Device
```
uart_device → uart (protocol)
           → sensor (if reading values)
```

## Testing Strategy

1. **Unit Test Each Stub Replacement**
   - Replace stub with real implementation
   - Test component loads without error
   - Test basic functionality

2. **Integration Test Dependency Chain**
   - Test components that depend on newly implemented component
   - Verify dependency resolution works correctly

3. **Platform Test**
   - Test on esp32 first (most common)
   - Test on esp8266 second
   - Test on alternative platforms as needed

## Quick Commands

```bash
# Regenerate stubs if needed
python3 script/stub_components.py

# Regenerate priority analysis
python3 script/prioritize_components.py

# Count implemented vs stubbed
grep -l "NOT IMPLEMENTED" embhome/components/*/__init__.py | wc -l

# Find components by type
grep "Platform types: sensor" embhome/components/*/__init__.py

# Find core-owned components
grep "Core-owned: YES" embhome/components/*/__init__.py
```

## Notes

- Stubs will raise `cv.Invalid` if referenced in config
- This prevents silent failures during development
- Replace stub content with real implementation as you progress
- Use dependency info to determine implementation order
- Scripts are reusable if ESPHome adds new components
