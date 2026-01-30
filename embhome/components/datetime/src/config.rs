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
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatetimeConfig {
    /// Component instance ID
    #[serde(skip_serializing_if = "Option::is_none")]
    pub id: Option<String<32>>,

    /// Human-readable name
    pub name: String<32>,

    /// Type of datetime entity
    #[serde(default = "default_type")]
    pub type_: DatetimeType,

    /// Update interval in seconds (optional)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub update_interval: Option<u64>,
}

fn default_type() -> DatetimeType {
    DatetimeType::Datetime
}

impl Default for DatetimeConfig {
    fn default() -> Self {
        Self {
            id: None,
            name: "Datetime".into(),
            type_: default_type(),
            update_interval: None,
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
