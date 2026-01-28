use core::ffi::c_void;
extern "C" {
    pub fn create_preferences_intervalsyncer_id() -> *mut c_void;
    pub fn create_my_dht() -> *mut c_void;
    pub fn create_interval_intervaltrigger_id() -> *mut c_void;
    pub fn call_cpp_loop(ptr: *mut c_void);
    pub fn i2c_bus_write(ptr: *mut c_void, address: u8, data: *const u8, len: usize) -> i32;
}

pub struct I2cShim { pub ptr: *mut c_void }
impl I2cShim {
    pub fn write(&self, address: u8, data: &[u8]) -> Result<(), ()> {
        unsafe { i2c_bus_write(self.ptr, address, data.as_ptr(), data.len()) };
        Ok(())
    }
}