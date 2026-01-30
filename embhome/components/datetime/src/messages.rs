//! Message and event types for datetime component

use embassy_sync::channel::Sender;
use crate::error::DatetimeError;

/// State of the datetime entity
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct DatetimeState {
    /// Year (1970-3000)
    pub year: Option<u16>,
    /// Month (1-12)
    pub month: Option<u8>,
    /// Day (1-31)
    pub day: Option<u8>,
    /// Hour (0-23)
    pub hour: Option<u8>,
    /// Minute (0-59)
    pub minute: Option<u8>,
    /// Second (0-59)
    pub second: Option<u8>,
    /// Timestamp in milliseconds since boot
    pub timestamp_ms: u64,
}

/// Messages that can be sent to datetime actor
#[derive(Clone)]
pub enum DatetimeMessage {
    /// Set the date
    SetDate { year: u16, month: u8, day: u8 },
    /// Set the time
    SetTime { hour: u8, minute: u8, second: u8 },
    /// Set both date and time
    SetDateTime {
        year: u16,
        month: u8,
        day: u8,
        hour: u8,
        minute: u8,
        second: u8,
    },
    /// Request current state
    GetState(Sender<'static, Result<DatetimeState, DatetimeError>, 1>),
    /// Graceful shutdown
    Shutdown,
}

/// Events emitted by datetime actor
#[derive(Debug, Clone)]
pub enum DatetimeEvent {
    /// Component is ready
    Ready,
    /// State has been updated
    StateChanged(DatetimeState),
    /// Error occurred
    Error(DatetimeError),
    /// Shutdown complete
    ShutdownComplete,
}
