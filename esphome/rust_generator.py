from esphome.core import CORE
from esphome.helpers import write_file_if_changed
import logging

_LOGGER = logging.getLogger(__name__)

def generate_bridge_cpp():
    code = ['#include "esphome.h"', '']

    # Generate Proxies for Rust components referenced by C++
    for component_id in CORE.rust_referenced_by_cpp:
        code.append(f"class {component_id}Proxy : public esphome::Component {{")
        code.append(f" public:")
        code.append(f"  void loop() override {{}}")
        code.append(f"  void turn_on() {{ /* call rust via FFI */ }}")
        code.append(f"}};")
        code.append(f"extern \"C\" void* create_{component_id}_proxy() {{")
        code.append(f"  return (void*) new {component_id}Proxy();")
        code.append(f"}}")

    code.append('extern "C" {')

    # Generate factory functions for legacy components
    for var in CORE.registered_components:
        component_id = str(var.base)
        # Check if it's NOT a rust component
        if component_id not in CORE.rust_component_ids:
            class_name = str(var.base.type)
            code.append(f"  void* create_{component_id}() {{")
            code.append(f"    return (void*) new {class_name}();")
            code.append(f"  }}")

    code.append('  void call_cpp_loop(void* ptr) {')
    code.append('    ((esphome::Component*)ptr)->loop();')
    code.append('  }')
    code.append('}')
    return "\n".join(code)

def generate_bridge_rs():
    code = ['use core::ffi::c_void;', 'extern "C" {']

    for var in CORE.registered_components:
        component_id = str(var.base)
        if component_id not in CORE.rust_component_ids:
            code.append(f"    pub fn create_{component_id}() -> *mut c_void;")

    code.append('    pub fn call_cpp_loop(ptr: *mut c_void);')
    code.append('    pub fn i2c_bus_write(ptr: *mut c_void, address: u8, data: *const u8, len: usize) -> i32;')
    code.append('}')
    code.append('')
    code.append('pub struct I2cShim { pub ptr: *mut c_void }')
    code.append('impl I2cShim {')
    code.append('    pub fn write(&self, address: u8, data: &[u8]) -> Result<(), ()> {')
    code.append('        unsafe { i2c_bus_write(self.ptr, address, data.as_ptr(), data.len()) };')
    code.append('        Ok(())')
    code.append('    }')
    code.append('}')
    return "\n".join(code)

def generate_main_rs():
    from esphome.pins import PIN_SCHEMA_REGISTRY
    legacy_pins = []
    for (key, _, number), pin_list in PIN_SCHEMA_REGISTRY.pins_used.items():
        is_rust = [str(cid) in CORE.rust_component_ids for _, cid, _ in pin_list]
        if not any(is_rust):
            legacy_pins.append(number)

    code = [
        '#![no_std]',
        '#![no_main]',
        '',
        'mod legacy_wrapper;',
        'mod registry;',
        'mod bridge;',
        '',
        'use embassy_executor::Spawner;',
        'use esp_backtrace as _;',
        'use esp_hal::clock::ClockControl;',
        'use esp_hal::peripherals::Peripherals;',
        'use esp_hal::prelude::*;',
        'use esp_hal::timer::TimerGroup;',
        'use esp_println::println;',
        'use legacy_wrapper::LegacyWrapper;',
        '',
        '#[embassy_executor::main]',
        'async fn main(spawner: Spawner) {',
        '    let peripherals = Peripherals::take();',
        f'    // Legacy pins: {legacy_pins}',
        '    let system = peripherals.SYSTEM.split();',
        '    let clocks = ClockControl::boot_defaults(system.clock_control).freeze();',
        '',
        '    let timg0 = TimerGroup::new(peripherals.TIMG0, &clocks);',
        '    esp_hal::embassy::init(&clocks, timg0.timer0);',
        '',
        '    println!("EmbHome starting...");',
        ''
    ]

    # Instantiate legacy components
    for var in CORE.registered_components:
        component_id = str(var.base)
        if component_id not in CORE.rust_component_ids:
            code.append(f'    let {component_id}_ptr = unsafe {{ bridge::create_{component_id}() }};')
            code.append(f'    registry::register_component("{component_id}", {component_id}_ptr);')
            code.append(f'    let mut {component_id}_wrapper = LegacyWrapper::new({component_id}_ptr);')
            # In a real implementation, we'd spawn a task for each
            # For simplicity in this spec, we'll just show the logic
            code.append(f'    // spawner.spawn(run_{component_id}({component_id}_wrapper)).unwrap();')

    code.append('')
    code.append('    loop {')
    code.append('        embassy_time::Timer::after(embassy_time::Duration::from_secs(1)).await;')
    code.append('    }')
    code.append('}')

    return "\n".join(code)

def write_rust_project():
    _LOGGER.info("Writing Rust project artifacts...")
    # The embhome directory should be in the root of the repo.
    # We use Path.cwd() to find it, assuming esphome is run from the root.
    from pathlib import Path
    root_path = Path.cwd()
    base_path = root_path / "embhome" / "src"

    write_file_if_changed(base_path / "bridge.rs", generate_bridge_rs())
    write_file_if_changed(base_path / "main.rs", generate_main_rs())
    # bridge.cpp goes into the C++ side of the build
    write_file_if_changed(root_path / "embhome" / "bridge.cpp", generate_bridge_cpp())
