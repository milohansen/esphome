//! Configuration types for datetime component

use serde::{Deserialize, Serialize};
use heapless::String;

/// Datetime configuration
///
/// Matches the ESPHome configuration schema.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatetimeConfig {
    /// Component instance ID
    #[serde(skip_serializing_if = "Option::is_none")]
    pub id: Option<String<32>>,

    /// Human-readable name
    pub name: String<32>,

    /// Icon for the entity
    #[serde(skip_serializing_if = "Option::is_none")]
    pub icon: Option<String<32>>,

    /// Reference to a Real Time Clock component
    #[serde(skip_serializing_if = "Option::is_none")]
    pub time_id: Option<String<32>>,

    /// Automation triggered when value changes
    /// Note: Handled by the core system via DatetimeEvent::StateChanged.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub on_value: Option<bool>,

    /// Automation triggered at specific time
    /// Note: Handled by the core system or external timer actors.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub on_time: Option<bool>,
}

impl Default for DatetimeConfig {
    fn default() -> Self {
        Self {
            id: None,
            name: "Datetime".into(),
            icon: None,
            time_id: None,
            on_value: None,
            on_time: None,
        }
    }
}

impl DatetimeConfig {
    /// Validate configuration
    pub fn validate(&self) -> Result<(), &'static str> {
        if self.name.is_empty() {
            return Err("Name cannot be empty");
        }
        Ok(())
    }
}
