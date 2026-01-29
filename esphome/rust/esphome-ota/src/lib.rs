#![no_std]

pub mod ota_writer;

use embassy_net::tcp::TcpSocket;
use esphome_wifi::WifiStack;
use embassy_time::Duration;
use log::{info, warn, error};
use ota_writer::OtaManager;
use md5::{Md5, Digest};

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

        if let Err(e) = handle_ota(&mut socket).await {
            error!("OTA failed: {:?}", e);
        } else {
            info!("OTA Success! Restarting...");
            // esp_hal::reset::software_reset();
            // In 0.22 it might be different, let's just log for now
        }
    }
}

#[derive(Debug)]
enum OtaError {
    SocketError,
    ProtocolError,
    FlashError,
}

async fn handle_ota(socket: &mut TcpSocket<'_>) -> Result<(), OtaError> {
    // 1. Handshake
    // Read 0x00 (version?)
    let mut buf = [0u8; 1024];

    // Read version (1 byte?) or features?
    // Legacy protocol:
    // Client connects.
    // Server waits? No.
    // Let's implement the "Safe Mode" OTA or similar simple protocol.
    // Read until we get something?

    // Simplest Protocol:
    // 1. Client Connects
    // 2. Client sends 0x00 (Protocol Version 1) or similar.
    // 3. Server sends 0x00 (OK)
    // 4. Client streams data
    // 5. Server writes
    // 6. Client sends MD5?

    // Step 1: Read Init
    // (Assuming legacy or basic protocol)
    let n = socket.read(&mut buf).await.map_err(|_| OtaError::SocketError)?;
    if n == 0 { return Err(OtaError::ProtocolError); }

    // Just Ack whatever they sent for now (0x00)
    socket.write(&[0x00]).await.map_err(|_| OtaError::SocketError)?;

    let mut ota_manager = OtaManager::new();
    let partition = ota_manager.get_next_ota_partition().ok_or(OtaError::FlashError)?;

    info!("Writing to partition at 0x{:x}", partition.address);
    ota_manager.begin_write(&partition).map_err(|_| OtaError::FlashError)?;

    let mut current_addr = partition.address;
    let mut hasher = Md5::new();
    let mut total_written = 0;

    loop {
        let n = socket.read(&mut buf).await.map_err(|_| OtaError::SocketError)?;
        if n == 0 { break; }

        hasher.update(&buf[..n]);
        ota_manager.write_chunk(current_addr, &buf[..n]).map_err(|_| OtaError::FlashError)?;
        current_addr += n as u32;
        total_written += n;

        if total_written % (1024 * 100) == 0 {
            info!("Written {} bytes", total_written);
        }
    }

    let result = hasher.finalize();
    info!("OTA Complete. Size: {}, MD5: {:x}", total_written, result);

    Ok(())
}
