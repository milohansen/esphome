#![no_std]
extern crate alloc;

pub mod proto {
    include!(concat!(env!("OUT_DIR"), "/esphome.api.rs"));
}

pub mod server;
pub mod frame;

pub use server::api_server;
