#![no_std]

use esphome_core::{Component, ComponentError};
use esphome_sensor::Sensor;
use embassy_time::{Duration, Instant, Timer};
use embassy_sync::channel::Receiver;
use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;

pub struct UptimeSensor {
    id: &'static str,
    sensor: Sensor,
    update_interval: Duration,
}

impl UptimeSensor {
    pub fn new(id: &'static str) -> Self {
        Self {
            id,
            sensor: Sensor::new(id),
            update_interval: Duration::from_secs(60),
        }
    }
}

#[async_trait::async_trait]
impl Component for UptimeSensor {
    type Message = ();
    type Config = Duration;

    fn id(&self) -> &str {
        self.id
    }

    async fn setup(&mut self, config: Self::Config) -> Result<(), ComponentError> {
        self.update_interval = config;
        Ok(())
    }

    async fn run(&mut self, _mailbox: Receiver<'static, CriticalSectionRawMutex, Self::Message, 8>) {
        let start_time = Instant::now();
        loop {
            let uptime_s = start_time.elapsed().as_secs() as f32;
            self.sensor.publish(uptime_s);
            Timer::after(self.update_interval).await;
        }
    }
}
