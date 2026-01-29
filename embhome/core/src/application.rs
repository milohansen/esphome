use crate::event_bus::EventBus;

/// Main application context
pub struct Application {
    /// Human-readable device name
    pub name: &'static str,

    /// Device platform (esp32, esp32c3, etc.)
    pub platform: Platform,

    /// Global event bus
    pub event_bus: EventBus,
}

impl Application {
    /// Create new application
    pub const fn new(name: &'static str, platform: Platform) -> Self {
        Self {
            name,
            platform,
            event_bus: EventBus::new(),
        }
    }

    /// Initialize application
    pub async fn init(&mut self) -> Result<(), AppError> {
        // In a real no_std implementation, logging init usually happens earlier or via a specific crate
        // For now, we assume logging is set up by the main entry point generated code

        log::info!("ESPHome-RS starting: {}", self.name);
        log::info!("Platform: {:?}", self.platform);

        Ok(())
    }
}

/// Platform enumeration
#[derive(Debug, Clone, Copy)]
pub enum Platform {
    Esp32,
    Esp32c3,
    Esp32s2,
    Esp32s3,
}

#[derive(Debug)]
pub enum AppError {
    InitializationFailed(&'static str),
}
