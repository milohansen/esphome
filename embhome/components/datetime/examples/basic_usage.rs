#![no_std]
#![no_main]

use embassy_executor::Spawner;
use embassy_sync::channel::Channel;
use embassy_time::{Duration, Timer};
use datetime_component::{
    DatetimeActor, DatetimeConfig, DatetimeMessage, DatetimeEvent, DatetimeType
};
use esp_backtrace as _;
use esp_println::println;

#[embassy_executor::task]
async fn datetime_task(
    actor: DatetimeActor,
    msg_rx: embassy_sync::channel::Receiver<'static, DatetimeMessage, 16>,
    evt_tx: embassy_sync::channel::Sender<'static, DatetimeEvent, 16>,
) {
    actor.run(msg_rx, evt_tx).await;
}

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    let _peripherals = esp_hal::init(esp_hal::Config::default());

    static MSG_CHANNEL: Channel<embassy_sync::blocking_mutex::raw::NoopRawMutex, DatetimeMessage, 16> = Channel::new();
    static EVT_CHANNEL: Channel<embassy_sync::blocking_mutex::raw::NoopRawMutex, DatetimeEvent, 16> = Channel::new();

    let mut config = DatetimeConfig::default();
    config.name = "Test Datetime".into();
    config.type_ = DatetimeType::Datetime;

    let actor = DatetimeActor::new(config);
    spawner.spawn(datetime_task(actor, MSG_CHANNEL.receiver(), EVT_CHANNEL.sender())).unwrap();

    let msg_tx = MSG_CHANNEL.sender();
    let mut evt_rx = EVT_CHANNEL.receiver();

    // Wait for ready
    if let DatetimeEvent::Ready = evt_rx.receive().await {
        println!("Datetime actor is ready!");
    }

    // Set a date and time
    msg_tx.send(DatetimeMessage::SetDateTime {
        year: 2024,
        month: 5,
        day: 20,
        hour: 10,
        minute: 30,
        second: 0,
    }).await;

    // Request state
    let (resp_tx, resp_rx) = Channel::<embassy_sync::blocking_mutex::raw::NoopRawMutex, _, 1>::new().split();
    msg_tx.send(DatetimeMessage::GetState(resp_tx)).await;

    if let Ok(state) = resp_rx.receive().await {
        println!("Confirmed state: {:04}-{:02}-{:02}",
            state.year.unwrap_or(0), state.month.unwrap_or(0), state.day.unwrap_or(0));
    }

    // Listen for events
    loop {
        match evt_rx.receive().await {
            DatetimeEvent::StateChanged(state) => {
                println!("Event: State changed to {:04}-{:02}-{:02} {:02}:{:02}:{:02}",
                    state.year.unwrap_or(0), state.month.unwrap_or(0), state.day.unwrap_or(0),
                    state.hour.unwrap_or(0), state.minute.unwrap_or(0), state.second.unwrap_or(0)
                );
            }
            DatetimeEvent::Error(e) => {
                println!("Error: {:?}", e);
            }
            _ => {}
        }
        Timer::after(Duration::from_secs(5)).await;
    }
}
