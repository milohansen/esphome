use core::ffi::c_void;
use embassy_futures::yield_now;

pub struct LegacyWrapper {
    cpp_ptr: *mut c_void,
}

extern "C" {
    fn call_cpp_loop(ptr: *mut c_void);
}

impl LegacyWrapper {
    pub fn new(cpp_ptr: *mut c_void) -> Self {
        Self { cpp_ptr }
    }

    pub async fn run(&mut self) {
        loop {
            unsafe {
                call_cpp_loop(self.cpp_ptr);
            }
            yield_now().await;
        }
    }
}
