//! Example usage of the I2C component
//!
//! These examples show common I2C usage patterns.

#![allow(unused)]

use crate::{I2CBus, I2CDevice};
use esp_hal::{
    gpio::Io,
    i2c::master::I2c as HalI2c,
    peripheral::Peripheral,
};

/// Example 1: Basic I2C bus initialization and scanning
pub fn example_scan(i2c: impl Peripheral<P = impl esp_hal::i2c::master::Instance>, io: Io) {
    let sda = io.pins.gpio21;
    let scl = io.pins.gpio22;

    let mut bus = I2CBus::new(i2c, sda, scl, 100_000);

    // Scan for devices
    let devices = bus.scan();
    for addr in devices {
        log::info!("Found device at 0x{:02X}", addr);
    }
}

/// Example 2: Read from an I2C device
pub fn example_read_device(i2c: impl Peripheral<P = impl esp_hal::i2c::master::Instance>, io: Io) {
    let sda = io.pins.gpio21;
    let scl = io.pins.gpio22;

    let mut bus = I2CBus::new(i2c, sda, scl, 100_000);

    // Create device wrapper for a sensor at address 0x76
    let mut device = I2CDevice::new(&mut bus, 0x76);

    // Read 2 bytes from device
    let mut buffer = [0u8; 2];
    if let Err(e) = device.read(&mut buffer) {
        log::error!("Failed to read from device: {:?}", e);
    }
}

/// Example 3: Read from a register
pub fn example_read_register(i2c: impl Peripheral<P = impl esp_hal::i2c::master::Instance>, io: Io) {
    let sda = io.pins.gpio21;
    let scl = io.pins.gpio22;

    let mut bus = I2CBus::new(i2c, sda, scl, 100_000);
    let mut device = I2CDevice::new(&mut bus, 0x76);

    // Read WHO_AM_I register (common pattern)
    match device.read_register_byte(0x00) {
        Ok(id) => log::info!("Device ID: 0x{:02X}", id),
        Err(e) => log::error!("Failed to read register: {:?}", e),
    }
}

/// Example 4: Write to a register
pub fn example_write_register(i2c: impl Peripheral<P = impl esp_hal::i2c::master::Instance>, io: Io) {
    let sda = io.pins.gpio21;
    let scl = io.pins.gpio22;

    let mut bus = I2CBus::new(i2c, sda, scl, 100_000);
    let mut device = I2CDevice::new(&mut bus, 0x76);

    // Write configuration to register 0x01
    if let Err(e) = device.write_register_byte(0x01, 0xA0) {
        log::error!("Failed to write register: {:?}", e);
    }
}

/// Example 5: Read/modify/write a register
pub fn example_modify_register(i2c: impl Peripheral<P = impl esp_hal::i2c::master::Instance>, io: Io) {
    let sda = io.pins.gpio21;
    let scl = io.pins.gpio22;

    let mut bus = I2CBus::new(i2c, sda, scl, 100_000);
    let mut device = I2CDevice::new(&mut bus, 0x76);

    // Set bit 3 in register 0x02
    if let Err(e) = device.set_bits(0x02, 0b0000_1000) {
        log::error!("Failed to set bits: {:?}", e);
    }

    // Clear bit 7 in register 0x02
    if let Err(e) = device.clear_bits(0x02, 0b1000_0000) {
        log::error!("Failed to clear bits: {:?}", e);
    }

    // Custom modification
    if let Err(e) = device.modify_register(0x02, |v| (v & 0xF0) | 0x05) {
        log::error!("Failed to modify register: {:?}", e);
    }
}

/// Example 6: Read 16-bit value from sensor
pub fn example_read_u16(i2c: impl Peripheral<P = impl esp_hal::i2c::master::Instance>, io: Io) {
    let sda = io.pins.gpio21;
    let scl = io.pins.gpio22;

    let mut bus = I2CBus::new(i2c, sda, scl, 100_000);
    let mut device = I2CDevice::new(&mut bus, 0x76);

    // Read 16-bit temperature value from registers 0x22-0x23
    match device.read_register_u16(0x22) {
        Ok(temp_raw) => {
            // Convert to temperature (example conversion)
            let temp_c = temp_raw as f32 / 100.0;
            log::info!("Temperature: {:.2}°C", temp_c);
        }
        Err(e) => log::error!("Failed to read temperature: {:?}", e),
    }
}

/// Example 7: Multiple devices on same bus
pub fn example_multiple_devices(i2c: impl Peripheral<P = impl esp_hal::i2c::master::Instance>, io: Io) {
    let sda = io.pins.gpio21;
    let scl = io.pins.gpio22;

    let mut bus = I2CBus::new(i2c, sda, scl, 100_000);

    // Device 1: BME280 sensor at 0x76
    let mut bme280 = I2CDevice::new(&mut bus, 0x76);
    let mut temp_data = [0u8; 3];
    let _ = bme280.read_register(0xFA, &mut temp_data);

    // Device 2: I/O expander at 0x20
    let mut io_expander = I2CDevice::new(&mut bus, 0x20);
    let _ = io_expander.write_register_byte(0x01, 0xFF);

    // Device 3: OLED display at 0x3C
    let mut oled = I2CDevice::new(&mut bus, 0x3C);
    let _ = oled.write(&[0x00, 0xAE]); // Display off command
}

/// Example 8: Using embedded-hal traits
pub fn example_embedded_hal(i2c: impl Peripheral<P = impl esp_hal::i2c::master::Instance>, io: Io) {
    use embedded_hal::i2c::I2c as _;

    let sda = io.pins.gpio21;
    let scl = io.pins.gpio22;

    let mut bus = I2CBus::new(i2c, sda, scl, 100_000);

    // Use embedded-hal trait methods
    let mut buffer = [0u8; 4];
    let _ = bus.read(0x76, &mut buffer);
    let _ = bus.write(0x76, &[0x01, 0x02, 0x03]);
    let _ = bus.write_read(0x76, &[0x00], &mut buffer);
}
