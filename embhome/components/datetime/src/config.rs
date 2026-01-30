//! Configuration types for datetime component

use serde::{Deserialize, Serialize};
use heapless::String;

/// Datetime component type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum DatetimeType {
    /// Date only (Year, Month, Day)
    Date,
    /// Time only (Hour, Minute, Second)
    Time,
    /// Date and Time
    Datetime,
}

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

    /// Type of datetime entity
    #[serde(default = "default_type", rename = "type")]
    pub type_: DatetimeType,

    /// Reference to a Real Time Clock component
    #[serde(skip_serializing_if = "Option::is_none")]
    pub time_id: Option<String<32>>,

    /// MQTT configuration ID
    #[serde(skip_serializing_if = "Option::is_none")]
    pub mqtt_id: Option<String<32>>,

    /// Web server configuration
    /// Note: Accepted in config but currently not functional in Rust actor.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub web_server: Option<bool>,

    /// Automation triggered when value changes
    /// Note: Handled by the core system via DatetimeEvent::StateChanged.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub on_value: Option<bool>,

    /// Automation triggered at specific time
    /// Note: Handled by the core system or external timer actors.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub on_time: Option<bool>,
}

fn default_type() -> DatetimeType {
    DatetimeType::Datetime
}

impl Default for DatetimeConfig {
    fn default() -> Self {
        Self {
            id: None,
            name: "Datetime".into(),
            icon: None,
            type_: default_type(),
            time_id: None,
            mqtt_id: None,
            web_server: None,
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
