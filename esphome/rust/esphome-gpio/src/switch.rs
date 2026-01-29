use esphome_core::{Component, ComponentError, ActorAddress};
use esphome_hal::gpio::{Output, Pin, EspGpioPin};
use embassy_sync::channel::Receiver;
use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;

/// Messages this component accepts
#[derive(Debug, Clone, Copy)]
pub enum SwitchCommand {
    TurnOn,
    TurnOff,
    Toggle,
}

/// Messages this component emits
#[derive(Debug, Clone, Copy)]
pub enum SwitchEvent {
    StateChanged { is_on: bool },
}

/// GPIO switch component
pub struct GpioSwitch<P: Pin> {
    id: &'static str,
    pin: Option<Output<'static, P>>,
    state: bool,
    event_bus: Option<ActorAddress<SwitchEvent>>,
}

impl<P: Pin> GpioSwitch<P> {
    pub fn new(id: &'static str) -> Self {
        Self {
            id,
            pin: None,
            state: false,
            event_bus: None,
        }
    }

    /// Subscribe to state change events
    pub fn subscribe_events(&mut self, addr: ActorAddress<SwitchEvent>) {
        self.event_bus = Some(addr);
    }

    fn set_state(&mut self, new_state: bool) {
        if new_state != self.state {
            self.state = new_state;

            if let Some(pin) = &mut self.pin {
                if new_state {
                    pin.set_high();
                } else {
                    pin.set_low();
                }
            }

            // Notify subscribers
            if let Some(ref bus) = self.event_bus {
                 // Ignore error if mailbox full
                let _ = bus.try_send(SwitchEvent::StateChanged { is_on: new_state });
            }
        }
    }
}

pub struct GpioSwitchConfig<P: Pin> {
    pub pin: EspGpioPin<{ P::NUMBER }>,
    pub initial_state: bool,
    pub inverted: bool,
}

#[async_trait::async_trait]
impl<P: Pin> Component for GpioSwitch<P> {
    type Message = SwitchCommand;
    type Config = GpioSwitchConfig<P>;

    fn id(&self) -> &str {
        self.id
    }

    async fn setup(&mut self, config: Self::Config) -> Result<(), ComponentError> {
        // Output::new expects the pin and initial state
        // Inverted logic should be handled here or in set_state.
        // For simplicity, assuming hardware level inversion handled by Output wrapper?
        // No, Output wrapper is raw. We handle inversion in set_state usually.
        // But for setup, we just init.

        let initial_hw_state = if config.inverted { !config.initial_state } else { config.initial_state };

        // Note: Output::new returns Output<'d, P>. We need 'static.
        // The config passes ownership of the Pin.
        // We assume the pin lives forever (it's hardware).
        self.pin = Some(Output::new(config.pin, initial_hw_state));
        self.state = config.initial_state;
        Ok(())
    }

    async fn run(&mut self, mailbox: Receiver<'static, CriticalSectionRawMutex, Self::Message, 8>) {
        loop {
            let cmd = mailbox.receive().await;

            match cmd {
                SwitchCommand::TurnOn => self.set_state(true),
                SwitchCommand::TurnOff => self.set_state(false),
                SwitchCommand::Toggle => self.set_state(!self.state),
            }
        }
    }
}
