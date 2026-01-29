use esphome_core::{Component, ComponentError, ActorAddress, SystemEvent};
use esphome_hal::gpio::{Input, Pin, EspGpioPin};
use embassy_sync::channel::Receiver;
use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;
use embassy_time::{Duration, Timer};

/// Messages this component emits
#[derive(Debug, Clone, Copy)]
pub enum BinarySensorEvent {
    StateChanged { state: bool },
}

/// GPIO binary sensor component
pub struct GpioBinarySensor<P: Pin> {
    id: &'static str,
    pin: Option<Input<'static, P>>,
    state: bool,
    subscribers: heapless::Vec<ActorAddress<BinarySensorEvent>, 4>,
}

impl<P: Pin> GpioBinarySensor<P> {
    pub fn new(id: &'static str) -> Self {
        Self {
            id,
            pin: None,
            state: false,
            subscribers: heapless::Vec::new(),
        }
    }

    pub fn subscribe(&mut self, addr: ActorAddress<BinarySensorEvent>) {
        let _ = self.subscribers.push(addr);
    }

    fn set_state(&mut self, new_state: bool) {
        if new_state != self.state {
            self.state = new_state;

            // Notify subscribers
            for sub in &self.subscribers {
                let _ = sub.try_send(BinarySensorEvent::StateChanged { state: new_state });
            }
        }
    }
}

pub struct GpioBinarySensorConfig<P: Pin> {
    pub pin: EspGpioPin<{ P::NUMBER }>,
    pub inverted: bool,
    pub pullup: bool,
    pub pulldown: bool,
}

#[async_trait::async_trait]
impl<P: Pin> Component for GpioBinarySensor<P> {
    type Message = (); // No incoming messages for now
    type Config = GpioBinarySensorConfig<P>;

    fn id(&self) -> &str {
        self.id
    }

    async fn setup(&mut self, config: Self::Config) -> Result<(), ComponentError> {
        let pull = if config.pullup {
            Some(true)
        } else if config.pulldown {
            Some(false)
        } else {
            None
        };

        self.pin = Some(Input::new(config.pin, pull));
        // Initial state
        if let Some(pin) = &self.pin {
             let raw_state = pin.is_high();
             self.state = if config.inverted { !raw_state } else { raw_state };
        }
        Ok(())
    }

    async fn run(&mut self, _mailbox: Receiver<'static, CriticalSectionRawMutex, Self::Message, 8>) {
        loop {
            if let Some(pin) = &self.pin {
                let raw_state = pin.is_high();
                // TODO: Handle inverted properly (should probably be in setup or a wrapper)
                self.set_state(raw_state);
            }
            Timer::after(Duration::from_millis(50)).await; // Poll every 50ms for now
        }
    }
}
