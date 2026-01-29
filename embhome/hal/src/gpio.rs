use core::marker::PhantomData;
pub use esp_hal::gpio::{Input as EspInput, Output as EspOutput, Level, Pull, GpioPin as EspGpioPin};

/// Marker trait for GPIO pins
pub trait Pin: Send + 'static {
    const NUMBER: u8;
}

/// Type-safe GPIO pin wrapper
pub struct GpioPin<const N: u8>;

impl<const N: u8> Pin for GpioPin<N> {
    const NUMBER: u8 = N;
}

/// Output pin wrapper
pub struct Output<'d, P: Pin> {
    inner: EspOutput<'d, EspGpioPin<{ P::NUMBER }>>,
    _pin: PhantomData<P>,
}

impl<'d, P: Pin> Output<'d, P> {
    pub fn new(pin: EspGpioPin<{ P::NUMBER }>, initial_output: bool) -> Self {
         let initial = if initial_output { Level::High } else { Level::Low };
         let inner = EspOutput::new(pin, initial);
         Self { inner, _pin: PhantomData }
    }

    pub fn set_high(&mut self) {
        self.inner.set_high();
    }

    pub fn set_low(&mut self) {
        self.inner.set_low();
    }
}

/// Input pin wrapper
pub struct Input<'d, P: Pin> {
    inner: EspInput<'d, EspGpioPin<{ P::NUMBER }>>,
    _pin: PhantomData<P>,
}

impl<'d, P: Pin> Input<'d, P> {
     pub fn new(pin: EspGpioPin<{ P::NUMBER }>, pull: Option<bool>) -> Self {
         let pull_mode = match pull {
             Some(true) => Pull::Up,
             Some(false) => Pull::Down,
             None => Pull::None,
         };
         let inner = EspInput::new(pin, pull_mode);
         Self { inner, _pin: PhantomData }
    }

    pub fn is_high(&self) -> bool {
        self.inner.is_high()
    }

    pub fn is_low(&self) -> bool {
        self.inner.is_low()
    }
}
