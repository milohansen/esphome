//! Datetime actor implementation

use embassy_futures::select::{select, Either};
use embassy_sync::channel::{Receiver, Sender};
use embassy_time::{Duration, Instant, Timer};
use log::{debug, info, warn};

use crate::{
    config::{DatetimeConfig, DatetimeType},
    error::DatetimeError,
    messages::{DatetimeEvent, DatetimeMessage, DatetimeState},
};

/// Datetime actor
pub struct DatetimeActor {
    config: DatetimeConfig,
    state: DatetimeState,
    initialized: bool,
}

impl DatetimeActor {
    /// Create new datetime actor
    pub fn new(config: DatetimeConfig) -> Self {
        Self {
            config,
            state: DatetimeState::default(),
            initialized: false,
        }
    }

    /// Main actor event loop
    pub async fn run(
        mut self,
        message_rx: Receiver<'static, DatetimeMessage, 16>,
        event_tx: Sender<'static, DatetimeEvent, 16>,
    ) -> ! {
        info!("Datetime actor '{}' starting", self.config.name);

        self.initialized = true;
        let _ = event_tx.send(DatetimeEvent::Ready).await;

        loop {
            let timeout = self.config.update_interval.map(Duration::from_secs);

            let result = if let Some(t) = timeout {
                match select(message_rx.receive(), Timer::after(t)).await {
                    Either::First(msg) => Some(msg),
                    Either::Second(_) => None, // Periodic tick
                }
            } else {
                Some(message_rx.receive().await)
            };

            if let Some(msg) = result {
                match msg {
                    DatetimeMessage::SetDate { year, month, day } => {
                        if let Err(e) = self.set_date(year, month, day) {
                            let _ = event_tx.send(DatetimeEvent::Error(e)).await;
                        } else {
                            let _ = event_tx.send(DatetimeEvent::StateChanged(self.state)).await;
                        }
                    }
                    DatetimeMessage::SetTime { hour, minute, second } => {
                        if let Err(e) = self.set_time(hour, minute, second) {
                            let _ = event_tx.send(DatetimeEvent::Error(e)).await;
                        } else {
                            let _ = event_tx.send(DatetimeEvent::StateChanged(self.state)).await;
                        }
                    }
                    DatetimeMessage::SetDateTime { year, month, day, hour, minute, second } => {
                        if let Err(e) = self.set_datetime(year, month, day, hour, minute, second) {
                            let _ = event_tx.send(DatetimeEvent::Error(e)).await;
                        } else {
                            let _ = event_tx.send(DatetimeEvent::StateChanged(self.state)).await;
                        }
                    }
                    DatetimeMessage::GetState(response_tx) => {
                        let _ = response_tx.send(Ok(self.state)).await;
                    }
                    DatetimeMessage::Shutdown => {
                        info!("Datetime actor '{}' shutting down", self.config.name);
                        let _ = event_tx.send(DatetimeEvent::ShutdownComplete).await;
                        // In a real system we might break the loop here if the executor supports it
                    }
                }
            } else {
                // Periodic task (if any)
                debug!("Datetime actor '{}' periodic tick", self.config.name);
            }
        }
    }

    fn set_date(&mut self, year: u16, month: u8, day: u8) -> Result<(), DatetimeError> {
        if self.config.type_ == DatetimeType::Time {
            return Err(DatetimeError::ConfigError);
        }
        self.validate_date(year, month, day)?;
        self.state.year = Some(year);
        self.state.month = Some(month);
        self.state.day = Some(day);
        self.state.timestamp_ms = Instant::now().as_millis();
        Ok(())
    }

    fn set_time(&mut self, hour: u8, minute: u8, second: u8) -> Result<(), DatetimeError> {
        if self.config.type_ == DatetimeType::Date {
            return Err(DatetimeError::ConfigError);
        }
        self.validate_time(hour, minute, second)?;
        self.state.hour = Some(hour);
        self.state.minute = Some(minute);
        self.state.second = Some(second);
        self.state.timestamp_ms = Instant::now().as_millis();
        Ok(())
    }

    fn set_datetime(&mut self, year: u16, month: u8, day: u8, hour: u8, minute: u8, second: u8) -> Result<(), DatetimeError> {
        if self.config.type_ != DatetimeType::Datetime {
            return Err(DatetimeError::ConfigError);
        }
        self.validate_date(year, month, day)?;
        self.validate_time(hour, minute, second)?;
        self.state.year = Some(year);
        self.state.month = Some(month);
        self.state.day = Some(day);
        self.state.hour = Some(hour);
        self.state.minute = Some(minute);
        self.state.second = Some(second);
        self.state.timestamp_ms = Instant::now().as_millis();
        Ok(())
    }

    fn validate_date(&self, year: u16, month: u8, day: u8) -> Result<(), DatetimeError> {
        if !(1970..=3000).contains(&year) {
            return Err(DatetimeError::InvalidYear);
        }
        if !(1..=12).contains(&month) {
            return Err(DatetimeError::InvalidMonth);
        }
        if day < 1 || day > days_in_month(month, year) {
            return Err(DatetimeError::InvalidDay);
        }
        Ok(())
    }

    fn validate_time(&self, hour: u8, minute: u8, second: u8) -> Result<(), DatetimeError> {
        if hour > 23 {
            return Err(DatetimeError::InvalidHour);
        }
        if minute > 59 {
            return Err(DatetimeError::InvalidMinute);
        }
        if second > 59 {
            return Err(DatetimeError::InvalidSecond);
        }
        Ok(())
    }
}

fn is_leap_year(year: u16) -> bool {
    (year % 4 == 0 && year % 100 != 0) || (year % 400 == 0)
}

fn days_in_month(month: u8, year: u16) -> u8 {
    match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 => {
            if is_leap_year(year) {
                29
            } else {
                28
            }
        }
        _ => 0,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_is_leap_year() {
        assert!(is_leap_year(2000));
        assert!(is_leap_year(2004));
        assert!(!is_leap_year(2100));
        assert!(!is_leap_year(2023));
    }

    #[test]
    fn test_days_in_month() {
        assert_eq!(days_in_month(1, 2024), 31);
        assert_eq!(days_in_month(2, 2024), 29);
        assert_eq!(days_in_month(2, 2023), 28);
        assert_eq!(days_in_month(4, 2024), 30);
    }

    #[test]
    fn test_validation() {
        let config = DatetimeConfig::default();
        let actor = DatetimeActor::new(config);

        assert!(actor.validate_date(2024, 2, 29).is_ok());
        assert!(actor.validate_date(2023, 2, 29).is_err());
        assert!(actor.validate_date(2024, 13, 1).is_err());
        assert!(actor.validate_date(1969, 12, 31).is_err());
        assert!(actor.validate_date(3001, 1, 1).is_err());

        assert!(actor.validate_time(23, 59, 59).is_ok());
        assert!(actor.validate_time(24, 0, 0).is_err());
        assert!(actor.validate_time(0, 60, 0).is_err());
        assert!(actor.validate_time(0, 0, 60).is_err());
    }
}
