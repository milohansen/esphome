use core::ffi::c_void;
use hashbrown::HashMap;
use critical_section::Mutex;
use core::cell::RefCell;

static REGISTRY: Mutex<RefCell<HashMap<&'static str, *mut c_void>>> = Mutex::new(RefCell::new(HashMap::new()));

pub fn register_component(id: &'static str, ptr: *mut c_void) {
    critical_section::with(|cs| {
        REGISTRY.borrow(cs).borrow_mut().insert(id, ptr);
    });
}

pub fn get_component(id: &str) -> Option<*mut c_void> {
    critical_section::with(|cs| {
        REGISTRY.borrow(cs).borrow().get(id).copied()
    })
}

#[no_mangle]
pub extern "C" fn esphome_register_cpp_component(id: *const core::ffi::c_char, ptr: *mut c_void) {
    // This would be called from C++ during initialization
    // For now, we assume the string is static or managed
    // In a real implementation, we'd need to handle string conversion/ownership
}
