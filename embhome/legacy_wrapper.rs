use core::ffi::c_void;
use core::marker::PhantomData;
use embassy_time::{Duration, Timer};

/// Wrapper for legacy C++ components to run them in an Embassy task.
///
/// Constrained to be !Send to ensure it stays on the single-threaded executor
/// where the global C++ state is safe to access.
pub struct LegacyWrapper {
    cpp_ptr: *mut c_void,
    id: &'static str,
    _not_send: PhantomData<*const ()>, // Makes it !Send
}

impl LegacyWrapper {
    pub fn new(ptr: *mut c_void, id: &'static str) -> Self {
        if ptr.is_null() {
            panic!("Attempted to wrap null component pointer for: {}", id);
        }
        Self {
            cpp_ptr: ptr,
            id,
            _not_send: PhantomData,
        }
    }

    /// The main loop for the legacy component.
    ///
    /// Calls the C++ setup() then loop() method and then yields.
    pub async fn run(&mut self) {
        unsafe {
            self.call_setup();
        }
        loop {
            unsafe {
                self.call_loop();
            }

            // Mandatory yield to prevent starving other tasks
            // and to allow the executor to process other components.
            embassy_futures::yield_now().await;
        }
    }

    /// Internal FFI call to the C++ setup() method.
    unsafe fn call_setup(&self) {
        extern "C" {
            fn call_component_setup(ptr: *mut c_void);
        }
        call_component_setup(self.cpp_ptr);
    }

    /// Internal FFI call to the C++ loop() method.
    unsafe fn call_loop(&self) {
        extern "C" {
            fn call_component_loop(ptr: *mut c_void);
        }
        call_component_loop(self.cpp_ptr);
    }
}

// Ensure LegacyWrapper is !Send
// (PhantomData<*const ()> already handles this, but we can be explicit if needed)
// impl !Send for LegacyWrapper {} // Requires nightly/unstable feature
