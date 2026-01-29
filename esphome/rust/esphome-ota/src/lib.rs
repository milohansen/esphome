#![no_std]

use embassy_net::tcp::TcpSocket;
use esphome_wifi::WifiStack;
use embassy_time::Duration;
use log::{info, warn, error};

#[embassy_executor::task]
pub async fn ota_server(stack: &'static WifiStack) {
    let mut rx_buffer = [0; 4096];
    let mut tx_buffer = [0; 4096];

    loop {
        let mut socket = TcpSocket::new(stack, &mut rx_buffer, &mut tx_buffer);
        socket.set_timeout(Some(Duration::from_secs(60)));

        info!("OTA Server listening on port 3232...");
        if let Err(e) = socket.accept(3232).await {
            warn!("Accept error: {:?}", e);
            continue;
        }

        info!("OTA Client connected from {:?}", socket.remote_endpoint());

        // TODO: Implement ESPHome OTA protocol
        // 1. Receive 0x00 (version)
        // 2. Receive 0x01 (password check)
        // 3. Receive binary size
        // 4. Stream to OTA partition
        // 5. Verify MD5
        // 6. Set boot partition
        // 7. Restart

        info!("OTA Update not yet fully implemented in Rust");
    }
}
