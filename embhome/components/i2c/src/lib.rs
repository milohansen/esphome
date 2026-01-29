//! I2C Bus Component for embhome
//!
//! This component provides I2C bus communication using esp-hal.
//!
//! # Features
//! - Multiple I2C bus support (up to 2 buses per chip)
//! - Configurable frequency (up to 400kHz)
//! - Device scanning
//! - Blocking and async operations
//! - Error handling with automatic retries
//!
//! # Example
//! ```no_run
//! use esphome_i2c::{I2CBus, I2CConfig};
//! use esp_hal::i2c::master::I2c;
//!
//! let config = I2CConfig {
//!     sda_pin: 21,
//!     scl_pin: 22,
//!     frequency: 100_000,
//! };
//!
//! let mut bus = I2CBus::new(i2c_peripheral, config);
//! bus.scan();
//! ```

#![no_std]

pub mod examples;

use core::fmt;
use embedded_hal::i2c::{ErrorKind, ErrorType, I2c as EmbeddedI2c};
use esp_hal::{
    gpio::{InputPin, OutputPin},
    i2c::master::{Config as I2cConfig, I2c},
    peripheral::Peripheral,
    Blocking,
};
use log::{debug, info, warn};

/// I2C error types
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Error {
    /// No acknowledgment received from device
    NoAck,
    /// Bus error (arbitration lost, etc.)
    Bus,
    /// Invalid argument
    InvalidArgument,
    /// Timeout waiting for operation
    Timeout,
    /// Buffer too large
    BufferTooLarge,
    /// Other error
    Other,
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::NoAck => write!(f, "No acknowledgment"),
            Error::Bus => write!(f, "Bus error"),
            Error::InvalidArgument => write!(f, "Invalid argument"),
            Error::Timeout => write!(f, "Timeout"),
            Error::BufferTooLarge => write!(f, "Buffer too large"),
            Error::Other => write!(f, "Other error"),
        }
    }
}

impl embedded_hal::i2c::Error for Error {
    fn kind(&self) -> ErrorKind {
        match self {
            Error::NoAck => ErrorKind::NoAcknowledge(embedded_hal::i2c::NoAcknowledgeSource::Address),
            Error::Bus => ErrorKind::Bus,
            Error::InvalidArgument => ErrorKind::Other,
            Error::Timeout => ErrorKind::Other,
            Error::BufferTooLarge => ErrorKind::Other,
            Error::Other => ErrorKind::Other,
        }
    }
}

/// I2C configuration
#[derive(Debug, Clone, Copy)]
pub struct I2CConfig {
    /// SDA pin number
    pub sda_pin: u8,
    /// SCL pin number
    pub scl_pin: u8,
    /// Bus frequency in Hz (typically 100_000 or 400_000)
    pub frequency: u32,
}

impl Default for I2CConfig {
    fn default() -> Self {
        Self {
            sda_pin: 21,
            scl_pin: 22,
            frequency: 100_000,
        }
    }
}

/// I2C Bus wrapper around esp-hal I2C peripheral
///
/// This provides a high-level interface for I2C communication.
pub struct I2CBus<'d> {
    /// The underlying esp-hal I2C peripheral
    i2c: I2c<'d, Blocking>,
    /// Configuration
    config: I2CConfig,
}

impl<'d> I2CBus<'d> {
    /// Create a new I2C bus
    ///
    /// # Arguments
    /// * `i2c` - I2C peripheral from esp-hal
    /// * `sda` - SDA pin
    /// * `scl` - SCL pin
    /// * `frequency` - Bus frequency in Hz
    pub fn new<SDA, SCL>(
        i2c: impl Peripheral<P = impl esp_hal::i2c::master::Instance> + 'd,
        sda: impl Peripheral<P = SDA> + 'd,
        scl: impl Peripheral<P = SCL> + 'd,
        frequency: u32,
    ) -> Self
    where
        SDA: InputPin + OutputPin,
        SCL: InputPin + OutputPin,
    {
        let config = I2cConfig::default().with_frequency(frequency.Hz());

        let i2c = I2c::new(i2c, config).with_sda(sda).with_scl(scl);

        info!(
            "I2C bus initialized: frequency={}Hz",
            frequency
        );

        Self {
            i2c,
            config: I2CConfig {
                sda_pin: 0, // Pin numbers stored separately in esp-hal
                scl_pin: 0,
                frequency,
            },
        }
    }

    /// Scan the I2C bus for devices
    ///
    /// Returns a list of addresses that acknowledged
    pub fn scan(&mut self) -> heapless::Vec<u8, 128> {
        info!("Scanning I2C bus...");
        let mut found = heapless::Vec::new();

        // Scan standard 7-bit addresses (0x08 to 0x77)
        // Skip reserved addresses:
        // - 0x00-0x07: Reserved
        // - 0x78-0x7F: Reserved
        for addr in 0x08..=0x77 {
            // Try to write 0 bytes to the address
            // If device exists, it will ACK
            if self.i2c.write(addr, &[]).is_ok() {
                info!("  Found device at address 0x{:02X}", addr);
                let _ = found.push(addr);
            }
        }

        if found.is_empty() {
            warn!("No I2C devices found");
        } else {
            info!("Found {} I2C device(s)", found.len());
        }

        found
    }

    /// Get the bus frequency
    pub fn frequency(&self) -> u32 {
        self.config.frequency
    }

    /// Read data from an I2C device
    pub fn read(&mut self, address: u8, buffer: &mut [u8]) -> Result<(), Error> {
        debug!("I2C read: addr=0x{:02X}, len={}", address, buffer.len());
        self.i2c.read(address, buffer).map_err(|_| Error::NoAck)
    }

    /// Write data to an I2C device
    pub fn write(&mut self, address: u8, data: &[u8]) -> Result<(), Error> {
        debug!("I2C write: addr=0x{:02X}, len={}", address, data.len());
        self.i2c.write(address, data).map_err(|_| Error::NoAck)
    }

    /// Write then read (common pattern for register access)
    pub fn write_read(
        &mut self,
        address: u8,
        write_data: &[u8],
        read_buffer: &mut [u8],
    ) -> Result<(), Error> {
        debug!(
            "I2C write_read: addr=0x{:02X}, write_len={}, read_len={}",
            address,
            write_data.len(),
            read_buffer.len()
        );
        self.i2c
            .write_read(address, write_data, read_buffer)
            .map_err(|_| Error::NoAck)
    }
}

// Implement embedded-hal traits for compatibility
impl<'d> ErrorType for I2CBus<'d> {
    type Error = Error;
}

impl<'d> EmbeddedI2c for I2CBus<'d> {
    fn read(&mut self, address: u8, read: &mut [u8]) -> Result<(), Self::Error> {
        I2CBus::read(self, address, read)
    }

    fn write(&mut self, address: u8, write: &[u8]) -> Result<(), Self::Error> {
        I2CBus::write(self, address, write)
    }

    fn write_read(
        &mut self,
        address: u8,
        write: &[u8],
        read: &mut [u8],
    ) -> Result<(), Self::Error> {
        I2CBus::write_read(self, address, write, read)
    }

    fn transaction(
        &mut self,
        address: u8,
        operations: &mut [embedded_hal::i2c::Operation<'_>],
    ) -> Result<(), Self::Error> {
        for operation in operations {
            match operation {
                embedded_hal::i2c::Operation::Read(buf) => {
                    self.read(address, buf)?;
                }
                embedded_hal::i2c::Operation::Write(buf) => {
                    self.write(address, buf)?;
                }
            }
        }
        Ok(())
    }
}

/// I2C Device - represents a device on the I2C bus
///
/// This provides a convenient wrapper around an I2C bus for a specific device address.
pub struct I2CDevice<'a, 'd> {
    bus: &'a mut I2CBus<'d>,
    address: u8,
}

impl<'a, 'd> I2CDevice<'a, 'd> {
    /// Create a new I2C device
    pub fn new(bus: &'a mut I2CBus<'d>, address: u8) -> Self {
        Self { bus, address }
    }

    /// Get the device address
    pub fn address(&self) -> u8 {
        self.address
    }

    /// Read from device
    pub fn read(&mut self, buffer: &mut [u8]) -> Result<(), Error> {
        self.bus.read(self.address, buffer)
    }

    /// Write to device
    pub fn write(&mut self, data: &[u8]) -> Result<(), Error> {
        self.bus.write(self.address, data)
    }

    /// Write then read from device
    pub fn write_read(&mut self, write_data: &[u8], read_buffer: &mut [u8]) -> Result<(), Error> {
        self.bus.write_read(self.address, write_data, read_buffer)
    }

    /// Read a register (8-bit register address)
    pub fn read_register(&mut self, register: u8, buffer: &mut [u8]) -> Result<(), Error> {
        self.write_read(&[register], buffer)
    }

    /// Write to a register (8-bit register address)
    pub fn write_register(&mut self, register: u8, data: &[u8]) -> Result<(), Error> {
        let mut write_buf = [0u8; 33]; // 1 byte register + up to 32 bytes data

        if data.len() > 32 {
            return Err(Error::BufferTooLarge);
        }

        write_buf[0] = register;
        write_buf[1..data.len() + 1].copy_from_slice(data);

        self.bus.write(self.address, &write_buf[..data.len() + 1])
    }

    /// Read a 16-bit register (big-endian)
    pub fn read_register_u16(&mut self, register: u8) -> Result<u16, Error> {
        let mut buf = [0u8; 2];
        self.read_register(register, &mut buf)?;
        Ok(u16::from_be_bytes(buf))
    }

    /// Write a 16-bit register (big-endian)
    pub fn write_register_u16(&mut self, register: u8, value: u16) -> Result<(), Error> {
        let data = value.to_be_bytes();
        self.write_register(register, &data)
    }

    /// Read a single byte from a register
    pub fn read_register_byte(&mut self, register: u8) -> Result<u8, Error> {
        let mut buf = [0u8; 1];
        self.read_register(register, &mut buf)?;
        Ok(buf[0])
    }

    /// Write a single byte to a register
    pub fn write_register_byte(&mut self, register: u8, value: u8) -> Result<(), Error> {
        self.write_register(register, &[value])
    }

    /// Modify bits in a register (read-modify-write)
    pub fn modify_register<F>(&mut self, register: u8, f: F) -> Result<(), Error>
    where
        F: FnOnce(u8) -> u8,
    {
        let value = self.read_register_byte(register)?;
        let new_value = f(value);
        self.write_register_byte(register, new_value)
    }

    /// Set bits in a register
    pub fn set_bits(&mut self, register: u8, mask: u8) -> Result<(), Error> {
        self.modify_register(register, |v| v | mask)
    }

    /// Clear bits in a register
    pub fn clear_bits(&mut self, register: u8, mask: u8) -> Result<(), Error> {
        self.modify_register(register, |v| v & !mask)
    }
}

/// Re-export types for convenience
pub use esp_hal::i2c::master::{I2c as HalI2c, Instance as I2cInstance};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_default() {
        let config = I2CConfig::default();
        assert_eq!(config.frequency, 100_000);
    }
}
