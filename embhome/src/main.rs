#![no_std]
#![no_main]

mod legacy_wrapper;
mod registry;
mod bridge;

use embassy_executor::Spawner;
use esp_backtrace as _;
use esp_hal::clock::ClockControl;
use esp_hal::peripherals::Peripherals;
use esp_hal::prelude::*;
use esp_hal::timer::TimerGroup;
use esp_println::println;
use legacy_wrapper::LegacyWrapper;

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    let peripherals = Peripherals::take();
    // Legacy pins: [4]
    let system = peripherals.SYSTEM.split();
    let clocks = ClockControl::boot_defaults(system.clock_control).freeze();

    let timg0 = TimerGroup::new(peripherals.TIMG0, &clocks);
    esp_hal::embassy::init(&clocks, timg0.timer0);

    println!("EmbHome starting...");

    let preferences_intervalsyncer_id_ptr = unsafe { bridge::create_preferences_intervalsyncer_id() };
    registry::register_component("preferences_intervalsyncer_id", preferences_intervalsyncer_id_ptr);
    let mut preferences_intervalsyncer_id_wrapper = LegacyWrapper::new(preferences_intervalsyncer_id_ptr);
    // spawner.spawn(run_preferences_intervalsyncer_id(preferences_intervalsyncer_id_wrapper)).unwrap();
    let my_dht_ptr = unsafe { bridge::create_my_dht() };
    registry::register_component("my_dht", my_dht_ptr);
    let mut my_dht_wrapper = LegacyWrapper::new(my_dht_ptr);
    // spawner.spawn(run_my_dht(my_dht_wrapper)).unwrap();
    let interval_intervaltrigger_id_ptr = unsafe { bridge::create_interval_intervaltrigger_id() };
    registry::register_component("interval_intervaltrigger_id", interval_intervaltrigger_id_ptr);
    let mut interval_intervaltrigger_id_wrapper = LegacyWrapper::new(interval_intervaltrigger_id_ptr);
    // spawner.spawn(run_interval_intervaltrigger_id(interval_intervaltrigger_id_wrapper)).unwrap();

    loop {
        embassy_time::Timer::after(embassy_time::Duration::from_secs(1)).await;
    }
}