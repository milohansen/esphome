use embassy_net::tcp::TcpSocket;
use embassy_net::Stack;
use esphome_wifi::WifiStack;
use crate::proto;
use crate::frame::{decode_frame, encode_frame, FrameError};
use prost::Message;
use log::{info, warn, error};
use embassy_time::{Duration, Timer};
use alloc::vec::Vec;
use embassy_net::IpListenEndpoint;

#[embassy_executor::task]
pub async fn api_server(stack: &'static WifiStack) {
    let mut rx_buffer = [0; 2048];
    let mut tx_buffer = [0; 2048];

    loop {
        let mut socket = TcpSocket::new(stack, &mut rx_buffer, &mut tx_buffer);
        socket.set_timeout(Some(Duration::from_secs(60)));

        info!("API Server listening on port 6053...");
        if let Err(e) = socket.accept(IpListenEndpoint { addr: None, port: 6053 }).await {
            warn!("Accept error: {:?}", e);
            continue;
        }

        info!("API Client connected from {:?}", socket.remote_endpoint());

        let mut read_buf = [0u8; 4096];
        let mut read_pos = 0;

        loop {
            match socket.read(&mut read_buf[read_pos..]).await {
                Ok(0) => {
                    info!("Client disconnected");
                    break;
                }
                Ok(n) => {
                    read_pos += n;

                    while read_pos > 0 {
                        match decode_frame(&read_buf[..read_pos]) {
                            Ok((frame, consumed)) => {
                                handle_frame(&mut socket, frame).await;

                                // Shift buffer
                                read_buf.copy_within(consumed..read_pos, 0);
                                read_pos -= consumed;
                            }
                            Err(FrameError::Incomplete) => break,
                            Err(_) => {
                                error!("Invalid frame, dropping connection");
                                break;
                            }
                        }
                    }
                }
                Err(e) => {
                    warn!("Read error: {:?}", e);
                    break;
                }
            }
        }
    }
}

async fn handle_frame(socket: &mut TcpSocket<'_>, frame: crate::frame::Frame) {
    // Message types are defined in api.proto
    // HelloRequest = 1
    // HelloResponse = 2
    // ConnectRequest = 3
    // ConnectResponse = 4
    // PingRequest = 5
    // PingResponse = 6

    match frame.msg_type {
        1 => { // HelloRequest
            let req = proto::HelloRequest::decode(&frame.payload[..]).unwrap();
            info!("Received HelloRequest from {}", req.client_info);

            let resp = proto::HelloResponse {
                api_version_major: 1,
                api_version_minor: 9,
                server_info: "ESPHome-RS".into(),
                name: "rust-device".into(),
            };

            send_proto(socket, 2, &resp).await;
        }
        3 => { // ConnectRequest
            let _req = proto::ConnectRequest::decode(&frame.payload[..]).unwrap();
            info!("Received ConnectRequest");

            let resp = proto::ConnectResponse {
                invalid_password: false,
            };

            send_proto(socket, 4, &resp).await;
        }
        5 => { // PingRequest
            let _req = proto::PingRequest::decode(&frame.payload[..]).unwrap();
            let resp = proto::PingResponse {};
            send_proto(socket, 6, &resp).await;
        }
        _ => {
            warn!("Unhandled msg_type: {}", frame.msg_type);
        }
    }
}

async fn send_proto<M: Message>(socket: &mut TcpSocket<'_>, msg_type: u32, msg: &M) {
    let mut payload = Vec::new();
    msg.encode(&mut payload).unwrap();

    let frame = encode_frame(msg_type, &payload);
    let _ = socket.write_all(&frame).await;
}
