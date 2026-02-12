use embassy_executor::task;
use esp_hal::gpio::{AnyPin, Output, Level, DriveStrength};
use embassy_sync::channel::Channel;
use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;

#[repr(C)]
#[derive(Clone, Copy)]
pub enum SwitchCommand {
    TurnOn,
    TurnOff,
    Toggle,
}

pub struct GpioSwitch {
    id: &'static str,
    pin: Output<'static, AnyPin>,
    command_channel: &'static Channel<CriticalSectionRawMutex, SwitchCommand, 8>,
    on_update: fn(bool),
}

impl GpioSwitch {
    pub fn new(
        id: &'static str,
        pin: AnyPin,
        initial_level: Level,
        command_channel: &'static Channel<CriticalSectionRawMutex, SwitchCommand, 8>,
        on_update: fn(bool)
    ) -> Self {
        let output = Output::new(pin, initial_level);
        Self {
            id,
            pin: output,
            command_channel,
            on_update,
        }
    }

    pub async fn run(&mut self) {
        loop {
            let cmd = self.command_channel.receive().await;
            match cmd {
                SwitchCommand::TurnOn => self.pin.set_high(),
                SwitchCommand::TurnOff => self.pin.set_low(),
                SwitchCommand::Toggle => self.pin.toggle(),
            }
            // Sync shadow state to C++
            self.update_shadow();
        }
    }

    fn update_shadow(&self) {
        let is_on = self.pin.is_set_high();
        (self.on_update)(is_on);
    }
}
