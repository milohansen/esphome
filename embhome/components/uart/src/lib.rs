//! UART Component for embhome
//!
//! Provides serial communication using esp-hal UART peripheral.

#![no_std]

use core::fmt;
use embedded_io::{ErrorType, Read, Write};
use esp_hal::{
    gpio::{InputPin, OutputPin},
    peripheral::Peripheral,
    uart::{
        config::{Config, DataBits, Parity, StopBits},
        Uart, UartRx, UartTx,
    },
    Blocking,
};
use log::{debug, info};

/// UART error types
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Error {
    /// No data available
    WouldBlock,
    /// Buffer overflow
    BufferOverflow,
    /// Parity error
    ParityError,
    /// Framing error
    FramingError,
    /// Break condition
    Break,
    /// Other error
    Other,
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::WouldBlock => write!(f, "Would block"),
            Error::BufferOverflow => write!(f, "Buffer overflow"),
            Error::ParityError => write!(f, "Parity error"),
            Error::FramingError => write!(f, "Framing error"),
            Error::Break => write!(f, "Break condition"),
            Error::Other => write!(f, "Other error"),
        }
    }
}

impl embedded_io::Error for Error {
    fn kind(&self) -> embedded_io::ErrorKind {
        match self {
            Error::WouldBlock => embedded_io::ErrorKind::WouldBlock,
            _ => embedded_io::ErrorKind::Other,
        }
    }
}

/// UART Component wrapping esp-hal UART
pub struct UARTComponent<'d> {
    uart: Uart<'d, Blocking>,
    config: UARTConfig,
}

/// UART configuration
#[derive(Debug, Clone, Copy)]
pub struct UARTConfig {
    pub baud_rate: u32,
    pub data_bits: DataBits,
    pub parity: Parity,
    pub stop_bits: StopBits,
}

impl Default for UARTConfig {
    fn default() -> Self {
        Self {
            baud_rate: 115200,
            data_bits: DataBits::DataBits8,
            parity: Parity::ParityNone,
            stop_bits: StopBits::STOP1,
        }
    }
}

impl<'d> UARTComponent<'d> {
    /// Create new UART component
    pub fn new<TX, RX>(
        uart: impl Peripheral<P = impl esp_hal::uart::Instance> + 'd,
        tx: impl Peripheral<P = TX> + 'd,
        rx: impl Peripheral<P = RX> + 'd,
        baud_rate: u32,
    ) -> Self
    where
        TX: OutputPin,
        RX: InputPin,
    {
        let config = Config::default().baudrate(baud_rate);
        let uart = Uart::new(uart, config).with_tx(tx).with_rx(rx);

        info!("UART initialized: baud_rate={}", baud_rate);

        Self {
            uart,
            config: UARTConfig {
                baud_rate,
                ..Default::default()
            },
        }
    }

    /// Create TX-only UART
    pub fn new_tx_only<TX>(
        uart: impl Peripheral<P = impl esp_hal::uart::Instance> + 'd,
        tx: impl Peripheral<P = TX> + 'd,
        baud_rate: u32,
    ) -> Self
    where
        TX: OutputPin,
    {
        let config = Config::default().baudrate(baud_rate);
        let uart = Uart::new(uart, config).with_tx(tx);

        info!("UART (TX-only) initialized: baud_rate={}", baud_rate);

        Self {
            uart,
            config: UARTConfig {
                baud_rate,
                ..Default::default()
            },
        }
    }

    /// Create RX-only UART
    pub fn new_rx_only<RX>(
        uart: impl Peripheral<P = impl esp_hal::uart::Instance> + 'd,
        rx: impl Peripheral<P = RX> + 'd,
        baud_rate: u32,
    ) -> Self
    where
        RX: InputPin,
    {
        let config = Config::default().baudrate(baud_rate);
        let uart = Uart::new(uart, config).with_rx(rx);

        info!("UART (RX-only) initialized: baud_rate={}", baud_rate);

        Self {
            uart,
            config: UARTConfig {
                baud_rate,
                ..Default::default()
            },
        }
    }

    /// Write a single byte
    pub fn write_byte(&mut self, byte: u8) -> Result<(), Error> {
        self.uart.write_byte(byte).map_err(|_| Error::Other)
    }

    /// Write multiple bytes
    pub fn write_bytes(&mut self, data: &[u8]) -> Result<(), Error> {
        self.uart.write_bytes(data).map_err(|_| Error::Other)
    }

    /// Read a single byte (blocking)
    pub fn read_byte(&mut self) -> Result<u8, Error> {
        self.uart.read_byte().map_err(|_| Error::WouldBlock)
    }

    /// Read multiple bytes (blocking until buffer is filled)
    pub fn read_bytes(&mut self, buffer: &mut [u8]) -> Result<usize, Error> {
        let mut count = 0;
        for byte in buffer.iter_mut() {
            match self.uart.read_byte() {
                Ok(b) => {
                    *byte = b;
                    count += 1;
                }
                Err(_) => break,
            }
        }
        if count > 0 {
            Ok(count)
        } else {
            Err(Error::WouldBlock)
        }
    }

    /// Check how many bytes are available
    pub fn available(&self) -> usize {
        self.uart.rx_fifo_count()
    }

    /// Flush TX buffer
    pub fn flush(&mut self) -> Result<(), Error> {
        self.uart.flush_tx().map_err(|_| Error::Other)
    }

    /// Get baud rate
    pub fn baud_rate(&self) -> u32 {
        self.config.baud_rate
    }
}

// Implement embedded-io traits
impl<'d> ErrorType for UARTComponent<'d> {
    type Error = Error;
}

impl<'d> Write for UARTComponent<'d> {
    fn write(&mut self, buf: &[u8]) -> Result<usize, Self::Error> {
        self.write_bytes(buf)?;
        Ok(buf.len())
    }

    fn flush(&mut self) -> Result<(), Self::Error> {
        UARTComponent::flush(self)
    }
}

impl<'d> Read for UARTComponent<'d> {
    fn read(&mut self, buf: &mut [u8]) -> Result<usize, Self::Error> {
        self.read_bytes(buf)
    }
}

/// UART Device - wrapper for a specific device using UART
pub struct UARTDevice<'a, 'd> {
    uart: &'a mut UARTComponent<'d>,
}

impl<'a, 'd> UARTDevice<'a, 'd> {
    /// Create new UART device
    pub fn new(uart: &'a mut UARTComponent<'d>) -> Self {
        Self { uart }
    }

    /// Write a byte
    pub fn write_byte(&mut self, byte: u8) -> Result<(), Error> {
        self.uart.write_byte(byte)
    }

    /// Write bytes
    pub fn write_bytes(&mut self, data: &[u8]) -> Result<(), Error> {
        self.uart.write_bytes(data)
    }

    /// Write a string
    pub fn write_str(&mut self, s: &str) -> Result<(), Error> {
        self.write_bytes(s.as_bytes())
    }

    /// Read a byte
    pub fn read_byte(&mut self) -> Result<u8, Error> {
        self.uart.read_byte()
    }

    /// Read multiple bytes
    pub fn read_bytes(&mut self, buffer: &mut [u8]) -> Result<usize, Error> {
        self.uart.read_bytes(buffer)
    }

    /// Check available bytes
    pub fn available(&self) -> usize {
        self.uart.available()
    }

    /// Flush TX buffer
    pub fn flush(&mut self) -> Result<(), Error> {
        self.uart.flush()
    }

    /// Read until delimiter or buffer full
    pub fn read_until(&mut self, delimiter: u8, buffer: &mut [u8]) -> Result<usize, Error> {
        let mut count = 0;
        for byte in buffer.iter_mut() {
            match self.read_byte() {
                Ok(b) => {
                    *byte = b;
                    count += 1;
                    if b == delimiter {
                        break;
                    }
                }
                Err(e) => {
                    if count > 0 {
                        break;
                    }
                    return Err(e);
                }
            }
        }
        Ok(count)
    }

    /// Read line (until '\n')
    pub fn read_line(&mut self, buffer: &mut [u8]) -> Result<usize, Error> {
        self.read_until(b'\n', buffer)
    }
}

impl<'a, 'd> ErrorType for UARTDevice<'a, 'd> {
    type Error = Error;
}

impl<'a, 'd> Write for UARTDevice<'a, 'd> {
    fn write(&mut self, buf: &[u8]) -> Result<usize, Self::Error> {
        self.write_bytes(buf)?;
        Ok(buf.len())
    }

    fn flush(&mut self) -> Result<(), Self::Error> {
        UARTDevice::flush(self)
    }
}

impl<'a, 'd> Read for UARTDevice<'a, 'd> {
    fn read(&mut self, buf: &mut [u8]) -> Result<usize, Self::Error> {
        self.read_bytes(buf)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_default() {
        let config = UARTConfig::default();
        assert_eq!(config.baud_rate, 115200);
    }
}
