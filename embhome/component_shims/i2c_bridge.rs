use core::slice;
use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;
use embassy_sync::mutex::Mutex;
use esp_hal::i2c::I2C;
use embedded_hal_async::i2c::I2c as I2cTrait;
use core::cell::OnceCell;

/// Shared async I2C bus
pub struct AsyncI2cBus {
    bus: Mutex<CriticalSectionRawMutex, I2C<'static, esp_hal::peripherals::I2C0>>,
}

impl AsyncI2cBus {
    pub fn new(i2c_peripheral: I2C<'static, esp_hal::peripherals::I2C0>) -> Self {
        Self {
            bus: Mutex::new(i2c_peripheral),
        }
    }

    pub async fn write(&self, addr: u8, bytes: &[u8]) -> Result<(), esp_hal::i2c::Error> {
        let mut bus = self.bus.lock().await;
        bus.write(addr, bytes).await
    }

    pub async fn read(&self, addr: u8, buffer: &mut [u8]) -> Result<(), esp_hal::i2c::Error> {
        let mut bus = self.bus.lock().await;
        bus.read(addr, buffer).await
    }

    pub async fn write_read(
        &self,
        addr: u8,
        bytes: &[u8],
        buffer: &mut [u8]
    ) -> Result<(), esp_hal::i2c::Error> {
        let mut bus = self.bus.lock().await;
        bus.write_read(addr, bytes, buffer).await
    }
}

// Global I2C bus instance
pub static I2C_BUS: OnceCell<AsyncI2cBus> = OnceCell::new();

// FFI Implementation called by C++ shim

#[no_mangle]
pub extern "C" fn rust_i2c_write(
    addr: u8,
    data: *const u8,
    len: usize
) -> i32 {
    if data.is_null() || len == 0 {
        return -1;
    }

    let bytes = unsafe { slice::from_raw_parts(data, len) };
    let bus_wrapper = I2C_BUS.get().expect("I2C bus not initialized");

    // CRITICAL: We use a blocking lock and blocking write here
    // In a single-threaded environment, we must ensure no one else is using the bus.
    // Since we are called from C++, we are in the main execution thread.

    // Safety: In single-threaded Embassy, we can use try_lock or a custom shared access
    // For simplicity, we assume we have exclusive access here because we are the only running task.

    // We need to get access to the underlying I2C peripheral in a blocking way.
    // This is tricky because it's wrapped in an Embassy Mutex.

    // Use embassy_futures::block_on for now but be aware of the risks
    embassy_futures::block_on(async {
        match bus_wrapper.write(addr, bytes).await {
            Ok(()) => 0,
            Err(_) => -1,
        }
    })
}

#[no_mangle]
pub extern "C" fn rust_i2c_read(
    addr: u8,
    buffer: *mut u8,
    len: usize
) -> i32 {
    if buffer.is_null() || len == 0 {
        return -1;
    }

    let buffer_slice = unsafe { slice::from_raw_parts_mut(buffer, len) };
    let bus = I2C_BUS.get().expect("I2C bus not initialized");

    embassy_futures::block_on(async {
        match bus.read(addr, buffer_slice).await {
            Ok(()) => 0,
            Err(_) => -1,
        }
    })
}

#[no_mangle]
pub extern "C" fn rust_i2c_write_read(
    addr: u8,
    write_data: *const u8,
    write_len: usize,
    read_buffer: *mut u8,
    read_len: usize,
) -> i32 {
    if write_data.is_null() || write_len == 0 || read_buffer.is_null() || read_len == 0 {
        return -1;
    }

    let write_bytes = unsafe { slice::from_raw_parts(write_data, write_len) };
    let read_slice = unsafe { slice::from_raw_parts_mut(read_buffer, read_len) };
    let bus = I2C_BUS.get().expect("I2C bus not initialized");

    embassy_futures::block_on(async {
        match bus.write_read(addr, write_bytes, read_slice).await {
            Ok(()) => 0,
            Err(_) => -1,
        }
    })
}
