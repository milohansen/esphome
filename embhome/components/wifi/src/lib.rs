#![no_std]
extern crate alloc;

use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;
use embassy_sync::channel::Channel;
use embassy_net::{Stack, Config as NetConfig, StackResources, Ipv4Address, Ipv4Cidr, StaticConfigV4};
use esp_wifi::wifi::{WifiDevice, WifiController, WifiStaDevice, WifiEvent, WifiState};
use embassy_time::{Duration, Timer};
use esphome_config::WifiConfig;
use log::{info, warn, error};

pub type WifiStack = Stack<WifiDevice<'static, WifiStaDevice>>;

#[embassy_executor::task]
pub async fn connection_task(mut controller: WifiController<'static>, config: WifiConfig) {
    info!("Starting WiFi connection task");
    info!("SSID: {}", config.ssid);

    loop {
        if esp_wifi::wifi::get_wifi_state() == WifiState::StaConnected {
            // wait until we're no longer connected
            controller.wait_for_event(WifiEvent::StaDisconnected).await;
            Timer::after(Duration::from_millis(5000)).await
        }

        if !matches!(controller.is_started(), Ok(true)) {
            let client_config = esp_wifi::wifi::Configuration::Client(
                esp_wifi::wifi::ClientConfiguration {
                    ssid: config.ssid.as_str().try_into().unwrap(),
                    password: config.password.as_str().try_into().unwrap(),
                    ..Default::default()
                }
            );
            controller.set_configuration(&client_config).unwrap();
            info!("Starting WiFi controller...");
            controller.start().await.unwrap();
        }

        info!("Connecting to WiFi...");
        match controller.connect().await {
            Ok(_) => {
                info!("WiFi Connected!");
                controller.wait_for_event(WifiEvent::StaDisconnected).await;
            }
            Err(e) => {
                warn!("Failed to connect: {:?}, retrying...", e);
                Timer::after(Duration::from_millis(5000)).await
            }
        }
    }
}

#[embassy_executor::task]
pub async fn net_task(stack: &'static WifiStack) {
    stack.run().await
}

// Helper struct to hold resources allocated in main (static)
pub struct WifiResources {
    pub stack_resources: StackResources<3>,
}

impl WifiResources {
    pub const fn new() -> Self {
        Self {
            stack_resources: StackResources::<3>::new(),
        }
    }
}
