//! Error types for datetime component

/// Errors that can occur with datetime component
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DatetimeError {
    /// Invalid year (must be 1970-3000)
    InvalidYear,
    /// Invalid month (must be 1-12)
    InvalidMonth,
    /// Invalid day for the given month and year
    InvalidDay,
    /// Invalid hour (must be 0-23)
    InvalidHour,
    /// Invalid minute (must be 0-59)
    InvalidMinute,
    /// Invalid second (must be 0-59)
    InvalidSecond,
    /// Component not initialized
    NotInitialized,
    /// RTC communication error
    RtcError,
    /// Configuration error
    ConfigError,
}

impl core::fmt::Display for DatetimeError {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        match self {
            Self::InvalidYear => write!(f, "Year must be between 1970 and 3000"),
            Self::InvalidMonth => write!(f, "Month must be between 1 and 12"),
            Self::InvalidDay => write!(f, "Invalid day for month/year"),
            Self::InvalidHour => write!(f, "Hour must be between 0 and 23"),
            Self::InvalidMinute => write!(f, "Minute must be between 0 and 59"),
            Self::InvalidSecond => write!(f, "Second must be between 0 and 59"),
            Self::NotInitialized => write!(f, "Component not initialized"),
            Self::RtcError => write!(f, "RTC communication error"),
            Self::ConfigError => write!(f, "Configuration error"),
        }
    }
}
