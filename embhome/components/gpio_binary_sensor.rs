use embassy_executor::task;
use esp_hal::gpio::{AnyPin, Input, Pull};
use embassy_time::{Duration, Timer};

pub struct GpioBinarySensor {
    id: &'static str,
    pin: Input<'static, AnyPin>,
    last_state: bool,
    on_update: fn(bool),
}

impl GpioBinarySensor {
    pub fn new(id: &'static str, pin: AnyPin, pull: Pull, on_update: fn(bool)) -> Self {
        let input = Input::new(pin, pull);
        Self {
            id,
            pin: input,
            last_state: false,
            on_update,
        }
    }

    pub async fn run(&mut self) {
        self.last_state = self.pin.is_high();
        self.update_shadow(self.last_state);

        loop {
            // Simple polling for now
            let current_state = self.pin.is_high();
            if current_state != self.last_state {
                self.last_state = current_state;
                self.update_shadow(current_state);
            }
            Timer::after(Duration::from_millis(50)).await;
        }
    }

    fn update_shadow(&self, state: bool) {
        (self.on_update)(state);
    }
}
