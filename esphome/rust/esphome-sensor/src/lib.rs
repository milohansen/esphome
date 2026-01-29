#![no_std]

use esphome_core::ActorAddress;

#[derive(Debug, Clone, Copy)]
pub enum SensorEvent {
    ValueUpdated { value: f32 },
}

pub struct Sensor {
    id: &'static str,
    value: f32,
    subscribers: heapless::Vec<ActorAddress<SensorEvent>, 4>,
}

impl Sensor {
    pub fn new(id: &'static str) -> Self {
        Self {
            id,
            value: f32::NAN,
            subscribers: heapless::Vec::new(),
        }
    }

    pub fn subscribe(&mut self, addr: ActorAddress<SensorEvent>) {
        let _ = self.subscribers.push(addr);
    }

    pub fn publish(&mut self, value: f32) {
        if value != self.value {
            self.value = value;
            for sub in &self.subscribers {
                let _ = sub.try_send(SensorEvent::ValueUpdated { value });
            }
        }
    }
}
