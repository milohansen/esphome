//! Datetime Component for ESP32
//!
//! This component provides an actor-based interface to manage date, time, and datetime entities.
//! It supports validation of input values and provides state update notifications.
//!
//! # Example YAML Configuration
//!
//! ```yaml
//! datetime:
//!   - platform: template
//!     name: "Target Date"
//!     type: DATE
//! ```

#![no_std]

pub mod actor;
pub mod config;
pub mod error;
pub mod messages;

pub use actor::DatetimeActor;
pub use config::{DatetimeConfig, DatetimeType};
pub use error::DatetimeError;
pub use messages::{DatetimeEvent, DatetimeMessage, DatetimeState};
