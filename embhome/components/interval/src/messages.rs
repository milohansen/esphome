use embassy_time::Duration;

#[derive(Debug, Clone, Copy)]
pub enum IntervalMessage {
    SetInterval(Duration),
}

#[derive(Debug, Clone, Copy)]
pub enum IntervalEvent {
    Ready,
    Triggered,
}
