use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IntervalConfig {
    pub interval_ms: u32,
    pub startup_delay_ms: u32,
}

impl Default for IntervalConfig {
    fn default() -> Self {
        Self {
            interval_ms: 1000,
            startup_delay_ms: 0,
        }
    }
}
