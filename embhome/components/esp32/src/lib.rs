//! ESP32 Platform HAL for embhome
//!
//! This crate provides the hardware abstraction layer for all ESP32 variants
//! using esp-hal. It initializes the platform, sets up clocks, and provides
//! access to peripherals.

#![no_std]

use critical_section::Mutex;
use core::cell::RefCell;
use esp_hal::{
    clock::ClockControl,
    peripherals::Peripherals,
    prelude::*,
    system::SystemControl,
    Delay,
};

#[cfg(feature = "esp32")]
use esp_hal::clock::CpuClock;

/// Platform configuration
pub struct PlatformConfig {
    /// CPU frequency in MHz
    pub cpu_frequency_mhz: u32,
}

impl Default for PlatformConfig {
    fn default() -> Self {
        Self {
            cpu_frequency_mhz: 160,
        }
    }
}

/// Global platform instance
static PLATFORM: Mutex<RefCell<Option<Platform>>> = Mutex::new(RefCell::new(None));

/// Platform HAL instance
pub struct Platform {
    pub delay: Delay,
    _config: PlatformConfig,
}

impl Platform {
    /// Initialize the ESP32 platform
    pub fn init(config: PlatformConfig) -> Self {
        let peripherals = Peripherals::take();
        let system = SystemControl::new(peripherals.SYSTEM);

        // Configure clocks based on the target variant
        let clocks = ClockControl::max(system.clock_control).freeze();

        let delay = Delay::new(&clocks);

        log::info!("ESP32 platform initialized");
        log::info!("CPU frequency: {} MHz", config.cpu_frequency_mhz);

        Self {
            delay,
            _config: config,
        }
    }

    /// Get a reference to the global platform instance
    pub fn get() -> &'static Mutex<RefCell<Option<Platform>>> {
        &PLATFORM
    }

    /// Initialize and store the global platform instance
    pub fn init_global(config: PlatformConfig) {
        let platform = Self::init(config);
        critical_section::with(|cs| {
            PLATFORM.borrow_ref_mut(cs).replace(platform);
        });
    }
}

/// Delay for a number of microseconds
pub fn delay_us(us: u32) {
    critical_section::with(|cs| {
        if let Some(platform) = PLATFORM.borrow_ref_mut(cs).as_mut() {
            platform.delay.delay_micros(us);
        }
    });
}

/// Delay for a number of milliseconds
pub fn delay_ms(ms: u32) {
    critical_section::with(|cs| {
        if let Some(platform) = PLATFORM.borrow_ref_mut(cs).as_mut() {
            platform.delay.delay_millis(ms);
        }
    });
}

/// Get CPU frequency in MHz
#[cfg(feature = "esp32")]
pub fn get_cpu_frequency_mhz() -> u32 {
    match CpuClock::get() {
        CpuClock::Clock80MHz => 80,
        CpuClock::Clock160MHz => 160,
        CpuClock::Clock240MHz => 240,
    }
}

#[cfg(not(feature = "esp32"))]
pub fn get_cpu_frequency_mhz() -> u32 {
    // For non-ESP32 variants, return the configured frequency
    // This is a simplified version; in practice you'd query the clock system
    critical_section::with(|cs| {
        PLATFORM
            .borrow_ref(cs)
            .as_ref()
            .map(|p| p._config.cpu_frequency_mhz)
            .unwrap_or(160)
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_platform_config_default() {
        let config = PlatformConfig::default();
        assert_eq!(config.cpu_frequency_mhz, 160);
    }
}
