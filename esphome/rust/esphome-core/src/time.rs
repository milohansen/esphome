use embassy_time::{Duration, Instant, Timer};

/// Periodic task runner
pub struct Interval {
    duration: Duration,
    next_tick: Instant,
}

impl Interval {
    /// Create new interval timer
    pub fn new(duration: Duration) -> Self {
        Self {
            duration,
            next_tick: Instant::now() + duration,
        }
    }

    /// Wait until next tick
    pub async fn tick(&mut self) {
        Timer::at(self.next_tick).await;
        self.next_tick += self.duration;
    }
}
