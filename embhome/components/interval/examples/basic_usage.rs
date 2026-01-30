use esphome_interval::{IntervalActor, IntervalConfig, IntervalEvent};
use esphome_core::ActorAddress;
use embassy_sync::channel::Channel;
use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;
use embassy_time::Duration;

#[embassy_executor::task]
async fn interval_example() {
    static MAILBOX: Channel<CriticalSectionRawMutex, esphome_interval::IntervalMessage, 8> = Channel::new();
    static EVENT_CHANNEL: Channel<CriticalSectionRawMutex, IntervalEvent, 8> = Channel::new();

    let mut actor = IntervalActor::new("example_interval");

    // Subscribe to events
    actor.subscribe(ActorAddress::new(EVENT_CHANNEL.sender()));

    let config = IntervalConfig {
        interval_ms: 1000,
        startup_delay_ms: 500,
    };

    actor.setup(config).await.unwrap();

    // In a real application, you would spawn actor.run in a separate task
    // or use select to run it alongside event handling.
    actor.run(MAILBOX.receiver()).await;
}

#[embassy_executor::task]
async fn event_handler() {
    // This task would listen to IntervalEvent::Triggered and perform actions
}

fn main() {}
