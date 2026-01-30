use esphome_core::ComponentError;

#[derive(Debug)]
pub enum IntervalError {
    ConfigError(&'static str),
}

impl From<IntervalError> for ComponentError {
    fn from(error: IntervalError) -> Self {
        match error {
            IntervalError::ConfigError(msg) => ComponentError::ConfigError(msg),
        }
    }
}
