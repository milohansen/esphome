use crate::config::IntervalConfig;
use crate::messages::{IntervalMessage, IntervalEvent};
use crate::error::IntervalError;
use esphome_core::{Component, ComponentError, ActorAddress};
use embassy_time::{Duration, Timer, Instant};
use embassy_sync::channel::Receiver;
use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;
use embassy_futures::select::{select, Either};
use log::{info, error};

pub struct IntervalActor {
    id: &'static str,
    interval: Duration,
    startup_delay: Duration,
    subscribers: heapless::Vec<ActorAddress<IntervalEvent>, 4>,
}

impl IntervalActor {
    pub fn new(id: &'static str) -> Self {
        Self {
            id,
            interval: Duration::from_secs(1),
            startup_delay: Duration::from_secs(0),
            subscribers: heapless::Vec::new(),
        }
    }

    pub fn subscribe(&mut self, addr: ActorAddress<IntervalEvent>) {
        if self.subscribers.push(addr).is_err() {
            error!("{}: Too many subscribers", self.id);
        }
    }

    fn publish(&self, event: IntervalEvent) {
        for sub in &self.subscribers {
            let _ = sub.try_send(event);
        }
    }
}

#[async_trait::async_trait]
impl Component for IntervalActor {
    type Message = IntervalMessage;
    type Config = IntervalConfig;

    fn id(&self) -> &str {
        self.id
    }

    async fn setup(&mut self, config: Self::Config) -> Result<(), ComponentError> {
        self.interval = Duration::from_millis(config.interval_ms as u64);
        self.startup_delay = Duration::from_millis(config.startup_delay_ms as u64);

        if self.interval.as_ticks() == 0 {
            return Err(IntervalError::ConfigError("Interval cannot be zero").into());
        }

        info!("{}: Setup complete. Interval: {}ms, Startup Delay: {}ms",
            self.id, self.interval.as_millis(), self.startup_delay.as_millis());

        Ok(())
    }

    async fn run(&mut self, mailbox: Receiver<'static, CriticalSectionRawMutex, Self::Message, 8>) {
        if self.startup_delay.as_ticks() > 0 {
            let end = Instant::now() + self.startup_delay;
            loop {
                let now = Instant::now();
                if now >= end { break; }
                match select(mailbox.receive(), Timer::at(end)).await {
                    Either::First(msg) => {
                        match msg {
                            IntervalMessage::SetInterval(d) => {
                                self.interval = d;
                            }
                        }
                    }
                    Either::Second(_) => break,
                }
            }
        }

        self.publish(IntervalEvent::Ready);

        loop {
            let next_trigger = Instant::now() + self.interval;
            loop {
                let now = Instant::now();
                if now >= next_trigger { break; }
                match select(mailbox.receive(), Timer::at(next_trigger)).await {
                    Either::First(msg) => {
                        match msg {
                            IntervalMessage::SetInterval(d) => {
                                self.interval = d;
                            }
                        }
                    }
                    Either::Second(_) => break,
                }
            }
            self.publish(IntervalEvent::Triggered);
        }
    }
}
