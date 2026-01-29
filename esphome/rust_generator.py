import logging
import os
from pathlib import Path
import shutil

from esphome.config import iter_component_configs
from esphome.const import CONF_ID, CONF_PLATFORM
from esphome.core import CORE
from esphome.helpers import indent, write_file_if_changed

_LOGGER = logging.getLogger(__name__)

# List of components that have native Rust implementations
NATIVE_COMPONENTS = {
    "gpio_switch": "GpioSwitch",
    "gpio_binary_sensor": "GpioBinarySensor",
}


def classify_components(config):
    legacy = []
    native = []
    for domain, component, conf in iter_component_configs(config):
        if isinstance(conf, list):
            for c in conf:
                platform = c.get(CONF_PLATFORM)
                if platform in NATIVE_COMPONENTS:
                    native.append((domain, component, c))
                else:
                    legacy.append((domain, component, c))
        else:
            platform = conf.get(CONF_PLATFORM)
            if platform in NATIVE_COMPONENTS:
                native.append((domain, component, conf))
            else:
                legacy.append((domain, component, conf))
    return legacy, native


async def capture_component_code(domain, component, conf):
    # Save current CORE state
    old_main = CORE.main_statements
    old_global = CORE.global_statements
    old_component_ids = CORE.component_ids.copy()
    CORE.main_statements = []
    CORE.global_statements = []

    # Monkey-patch register_variable to avoid "already registered" errors
    old_register = CORE.register_variable
    CORE.register_variable = lambda id, obj: None

    from esphome import cpp_helpers
    import esphome.codegen as cg_module

    old_register_component = cpp_helpers.register_component
    old_cg_register_component = cg_module.register_component

    async def dummy_register_component(var, config):
        return var

    cpp_helpers.register_component = dummy_register_component
    cg_module.register_component = dummy_register_component

    try:
        # Run to_code
        await component.to_code(conf)
    finally:
        # Restore monkey-patches
        CORE.register_variable = old_register
        cpp_helpers.register_component = old_register_component
        cg_module.register_component = old_cg_register_component

    # Capture generated code
    setup_code = CORE.cpp_main_section
    global_code = CORE.cpp_global_section

    # Restore CORE state
    CORE.main_statements = old_main
    CORE.global_statements = old_global
    CORE.component_ids = old_component_ids

    return setup_code, global_code


def generate_bridge_cpp(legacy_info, native_info):
    code = []
    code.append('#include "esphome.h"')
    code.append("#include <cstdint>")
    code.append("#include <atomic>")
    code.append("")

    # Native Component Proxies
    for comp_id, info in native_info.items():
        if info["platform"] == "gpio_switch":
            code.append(f"class {comp_id}Proxy : public esphome::switch_::Switch {{")
            code.append(" public:")
            code.append("  void write_state(bool state) override {")
            code.append(f"    extern void rust_set_{comp_id}_state(bool state);")
            code.append(
                "    rust_set_@comp_id@_state(state);".replace("@comp_id@", comp_id)
            )
            code.append("  }")
            code.append("  std::atomic<bool> shadow_state{false};")
            code.append("};")
            code.append(f"{comp_id}Proxy* {comp_id}_proxy = new {comp_id}Proxy();")
        elif info["platform"] == "gpio_binary_sensor":
            code.append(
                f"class {comp_id}Proxy : public esphome::binary_sensor::BinarySensor {{"
            )
            code.append(" public:")
            code.append("  std::atomic<bool> shadow_state{false};")
            code.append("};")
            code.append(f"{comp_id}Proxy* {comp_id}_proxy = new {comp_id}Proxy();")
    code.append("")

    # All captured globals for legacy
    for comp_id, info in legacy_info.items():
        code.append(f"// Globals for {comp_id}")
        code.append(info["global_code"])

    code.append('extern "C" {')
    code.append("")

    # Generic loop caller
    code.append("void call_component_loop(void* component_ptr) {")
    code.append(
        "    auto* component = static_cast<esphome::Component*>(component_ptr);"
    )
    code.append("    component->loop();")
    code.append("}")
    code.append("")

    # Generic setup caller
    code.append("void call_component_setup(void* component_ptr) {")
    code.append(
        "    auto* component = static_cast<esphome::Component*>(component_ptr);"
    )
    code.append("    component->setup();")
    code.append("}")
    code.append("")

    # Factory functions for legacy components
    for comp_id, info in legacy_info.items():
        code.append(f"void* create_{comp_id}() {{")
        code.append(indent(info["setup_code"]))
        code.append(f"    return static_cast<void*>({comp_id});")
        code.append("}")
        code.append("")

    # Shadow update functions for native components
    for comp_id, info in native_info.items():
        code.append(f"void update_shadow_{comp_id}(bool state) {{")
        code.append(
            f"    {comp_id}_proxy->shadow_state.store(state, std::memory_order_relaxed);"
        )
        code.append(f"    {comp_id}_proxy->publish_state(state);")
        code.append("}")
        code.append("")

    code.append('} // extern "C"')
    return "\n".join(code)


def generate_bridge_rs(legacy_info, native_info):
    code = []
    code.append("use core::ffi::c_void;")
    code.append("pub use crate::component_shims::i2c_bridge::{AsyncI2cBus, I2C_BUS};")
    code.append("")
    code.append('extern "C" {')
    code.append("    pub fn call_component_loop(ptr: *mut c_void);")
    code.append("    pub fn call_component_setup(ptr: *mut c_void);")
    code.extend(
        [f"    pub fn create_{comp_id}() -> *mut c_void;" for comp_id in legacy_info]
    )
    code.append("}")
    code.append("")

    # Static lookup
    code.append("pub static mut LEGACY_COMPONENTS: &[(&str, *mut c_void)] = &[];")
    code.append("")
    code.append("pub fn get_legacy_component(id: &str) -> Option<*mut c_void> {")
    code.append("    unsafe {")
    code.append("        for (comp_id, ptr) in LEGACY_COMPONENTS {")
    code.append("            if *comp_id == id { return Some(*ptr); }")
    code.append("        }")
    code.append("    }")
    code.append("    None")
    code.append("}")

    # Shadow update FFI
    code.extend(
        [
            f'extern "C" {{ pub fn update_shadow_{comp_id}(state: bool); }}'
            for comp_id in native_info
        ]
    )

    # FFI for C++ calling Rust
    for comp_id, info in native_info.items():
        if info["platform"] == "gpio_switch":
            code.append(
                f"pub static {comp_id.upper()}_CMD: Channel<CriticalSectionRawMutex, crate::components::gpio_switch::SwitchCommand, 8> = Channel::new();"
            )
            code.append("#[no_mangle]")
            code.append(f'pub extern "C" fn rust_set_{comp_id}_state(state: bool) {{')
            code.append(
                "    let cmd = if state { crate::components::gpio_switch::SwitchCommand::TurnOn } else { crate::components::gpio_switch::SwitchCommand::TurnOff };"
            )
            code.append(f"    let _ = {comp_id.upper()}_CMD.try_send(cmd);")
            code.append("}")

    return "\n".join(code)


def generate_cargo_toml(name):
    return f"""
[package]
name = "{name}"
version = "0.1.0"
edition = "2024"

[dependencies]
embassy-executor = {{ version = "0.9.1", features = ["executor-thread", "task-arena-size-12288"] }}
embassy-time = {{ version = "0.5.0", features = ["generic-queue-8"] }}
embassy-sync = "0.7.2"
embassy-futures = "0.1.1"
embedded-hal = "1.0"
embedded-hal-async = "1.0"
# TODO: set target-features for the actual board being used
esp-hal = {{ version = "1.0.0", features = ["esp32"] }}
esp-hal-embassy = {{ version = "0.9.1", features = ["esp32", "executors"] }}
esp-backtrace = {{ version = "0.18.1", features = ["esp32", "panic-handler", "println"] }}
esp-println = {{ version = "0.16.1", features = ["esp32", "log"] }}
log = "0.4"
static_cell = "2.1"
critical-section = "1.2"

[build-dependencies]
bindgen = "0.72"
embuild = "0.33.1"
cc = "1.0"

[profile.release]
opt-level = "s"
lto = "fat"
codegen-units = 1
panic = "abort"
"""


def generate_build_rs():
    return """
use std::env;
use std::path::PathBuf;
use std::process::Command;

fn main() {
    // Step 1: Trigger C++ compilation via ESPHome's build system
    // For this migration, we assume the C++ side is built into libesphome.a

    // Step 2: Compile bridge.cpp and shims
    cc::Build::new()
        .cpp(true)
        .file("bridge.cpp")
        .file("component_shims/i2c_shim.cpp")
        .include("../src") // Path to esphome headers
        .compile("bridge_shims");

    // Step 3: Generate Rust FFI bindings from bridge.h
    let bindings = bindgen::Builder::default()
        .header("bridge.h")
        .clang_arg("-I../src")
        .parse_callbacks(Box::new(bindgen::CargoCallbacks))
        .generate()
        .expect("Unable to generate bindings");

    let out_path = PathBuf::from(env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out_path.join("bindings.rs"))
        .expect("Couldn't write bindings");

    // Step 4: Link the C++ static library
    // Path should be where libesphome.a is generated
    println!("cargo:rustc-link-search=native=../src/.pio/build/esp32dev");
    println!("cargo:rustc-link-lib=static=esphome");
    println!("cargo:rustc-link-lib=stdc++");

    // ESP32-specific linking
    println!("cargo:rustc-link-arg=-Wl,--whole-archive");
    println!("cargo:rustc-link-arg=-libesphome.a");
    println!("cargo:rustc-link-arg=-Wl,--no-whole-archive");
}
"""


def has_i2c(config):
    return "i2c" in config


def generate_main_rs(config, legacy_info, native_info):
    code = []
    code.append("#![no_std]")
    code.append("#![no_main]")
    code.append("")
    code.append("use embassy_executor::Spawner;")
    code.append("use esp_backtrace as _;")
    code.append("use esp_hal::{")
    code.append("    clock::ClockControl,")
    code.append("    peripherals::Peripherals,")
    code.append("    prelude::*,")
    code.append("    timer::TimerGroup,")
    code.append("    IO,")
    code.append("};")
    code.append("")
    code.append("mod bridge;")
    code.append("mod legacy_wrapper;")
    code.append("mod component_shims;")
    code.append("mod components;")
    code.append("")
    code.append("use legacy_wrapper::LegacyWrapper;")
    code.append("")
    code.append("#[main]")
    code.append("async fn main(spawner: Spawner) {")
    code.append("    let peripherals = Peripherals::take();")
    code.append("    let system = peripherals.SYSTEM.split();")
    code.append("    let clocks = ClockControl::max(system.clock_control).freeze();")
    code.append("")
    code.append("    let timer_group0 = TimerGroup::new(peripherals.TIMG0, &clocks);")
    # Embassy init for esp-hal
    code.append("    esp_hal_embassy::init(&clocks, timer_group0);")
    code.append("")
    code.append("    let io = IO::new(peripherals.GPIO, peripherals.IO_MUX);")
    code.append("")

    if has_i2c(config):
        i2c_configs = config["i2c"]
        if not isinstance(i2c_configs, list):
            i2c_configs = [i2c_configs]

        for i, i2c_conf in enumerate(i2c_configs):
            # Default pins for ESP32 if not specified
            sda = i2c_conf.get("sda", 21)
            scl = i2c_conf.get("scl", 22)
            freq = str(i2c_conf.get("frequency", "100kHz")).lower().replace("khz", "")

            code.append(f"    // Initialize I2C bus {i}")
            periph = f"I2C{i}" if i == 0 else f"I2C{i}"  # ESP32 has I2C0 and I2C1
            code.append(f"    let i2c{i} = esp_hal::i2c::I2C::new(")
            code.append(f"        peripherals.{periph},")
            code.append(f"        io.pins.gpio{sda},")
            code.append(f"        io.pins.gpio{scl},")
            code.append(f"        {freq}.kHz(),")
            code.append("        &clocks")
            code.append("    );")
            if i == 0:
                code.append(f"    let async_i2c = bridge::AsyncI2cBus::new(i2c{i});")
                code.append("    bridge::I2C_BUS.set(async_i2c).unwrap();")
            code.append("")

    legacy_ptrs = []
    for comp_id in legacy_info:
        code.append(f"    let {comp_id}_ptr = unsafe {{ bridge::create_{comp_id}() }};")
        code.append(f"    if !{comp_id}_ptr.is_null() {{")
        code.append(
            f'        let {comp_id}_wrapper = LegacyWrapper::new({comp_id}_ptr, "{comp_id}");'
        )
        code.append(
            f"        spawner.spawn(run_legacy_component({comp_id}_wrapper)).unwrap();"
        )
        code.append("    }")
        legacy_ptrs.append(f'("{comp_id}", {comp_id}_ptr)')

    if legacy_ptrs:
        code.append(
            f"    unsafe {{ bridge::LEGACY_COMPONENTS = &[{', '.join(legacy_ptrs)}]; }}"
        )

    # Instantiate native components
    for comp_id, info in native_info.items():
        if info["platform"] == "gpio_switch":
            pin = info["conf"].get("pin", 0)
            code.append(
                f"    let mut {comp_id} = crate::components::gpio_switch::GpioSwitch::new("
            )
            code.append(
                f'        "{comp_id}", io.pins.gpio{pin}.into(), esp_hal::gpio::Level::Low,'
            )
            code.append(
                f"        &bridge::{comp_id.upper()}_CMD, bridge::update_shadow_{comp_id}"
            )
            code.append("    );")
            code.append(f"    spawner.spawn(run_{comp_id}({comp_id})).unwrap();")
        elif info["platform"] == "gpio_binary_sensor":
            pin = info["conf"].get("pin", 0)
            code.append(
                f"    let mut {comp_id} = crate::components::gpio_binary_sensor::GpioBinarySensor::new("
            )
            code.append(
                f'        "{comp_id}", io.pins.gpio{pin}.into(), esp_hal::gpio::Pull::Up,'
            )
            code.append(f"        bridge::update_shadow_{comp_id}")
            code.append("    );")
            code.append(f"    spawner.spawn(run_{comp_id}({comp_id})).unwrap();")

    code.append("}")
    code.append("")

    # Native component tasks
    for comp_id, info in native_info.items():
        if info["platform"] == "gpio_switch":
            code.append("#[embassy_executor::task]")
            code.append(
                f"async fn run_{comp_id}(mut component: crate::components::gpio_switch::GpioSwitch) {{"
            )
            code.append("    component.run().await;")
            code.append("}")
        elif info["platform"] == "gpio_binary_sensor":
            code.append("#[embassy_executor::task]")
            code.append(
                f"async fn run_{comp_id}(mut component: crate::components::gpio_binary_sensor::GpioBinarySensor) {{"
            )
            code.append("    component.run().await;")
            code.append("}")
    code.append("")
    code.append("#[embassy_executor::task]")
    code.append("async fn run_legacy_component(mut wrapper: LegacyWrapper) {")
    code.append("    wrapper.run().await;")
    code.append("}")

    return "\n".join(code)


async def generate(config):
    _LOGGER.info("Generating Rust migration bridge...")
    legacy, native = classify_components(config)

    _LOGGER.info(
        "Classified components: %d legacy, %d native", len(legacy), len(native)
    )

    legacy_info = {}
    for name, component, conf in legacy:
        comp_id = conf.get(CONF_ID)
        if comp_id:
            setup_code, global_code = await capture_component_code(
                name, component, conf
            )
            legacy_info[str(comp_id)] = {
                "setup_code": setup_code,
                "global_code": global_code,
            }

    _LOGGER.info("Captured %d legacy components", len(legacy_info))

    native_info = {}
    for domain, component, conf in native:
        comp_id = conf.get(CONF_ID)
        if comp_id:
            native_info[str(comp_id)] = {
                "platform": conf.get(CONF_PLATFORM),
                "conf": conf,
            }

    # Use build path from CORE
    build_dir = Path(CORE.build_path) / "rust"
    build_dir.mkdir(parents=True, exist_ok=True)

    # bridge.cpp
    write_file_if_changed(
        build_dir / "bridge.cpp", generate_bridge_cpp(legacy_info, native_info)
    )
    # bridge.h (needed for bindgen)
    write_file_if_changed(
        build_dir / "bridge.h",
        '#include "esphome.h"\nextern "C" {\nvoid call_component_loop(void* ptr);\nvoid call_component_setup(void* ptr);\n}\n',
    )
    # bridge.rs
    write_file_if_changed(
        build_dir / "bridge.rs", generate_bridge_rs(legacy_info, native_info)
    )
    # main.rs
    write_file_if_changed(
        build_dir / "main.rs", generate_main_rs(config, legacy_info, native_info)
    )
    # Cargo.toml
    write_file_if_changed(build_dir / "Cargo.toml", generate_cargo_toml(CORE.name))
    # build.rs
    write_file_if_changed(build_dir / "build.rs", generate_build_rs())

    # Copy shared files from embhome/ to the build directory
    embhome_dir = Path("embhome")
    for file in ["legacy_wrapper.rs"]:
        shutil.copy(embhome_dir / file, build_dir / file)

    # Copy shims
    shims_dir = build_dir / "component_shims"
    shims_dir.mkdir(exist_ok=True)
    for file in os.listdir(embhome_dir / "component_shims"):
        shutil.copy(embhome_dir / "component_shims" / file, shims_dir / file)

    # Copy native components
    comp_dir = build_dir / "components"
    comp_dir.mkdir(exist_ok=True)
    for file in os.listdir(embhome_dir / "components"):
        shutil.copy(embhome_dir / "components" / file, comp_dir / file)

    # Create components/mod.rs
    with open(comp_dir / "mod.rs", "w") as f:
        for file in os.listdir(comp_dir):
            if file.endswith(".rs") and file != "mod.rs":
                f.write(f"pub mod {file[:-3]};\n")

    # Create component_shims/mod.rs
    with open(shims_dir / "mod.rs", "w") as f:
        for file in os.listdir(shims_dir):
            if file.endswith(".rs") and file != "mod.rs":
                f.write(f"pub mod {file[:-3]};\n")

    _LOGGER.info("Rust migration project generated in %s", build_dir)


def compile(config):
    build_dir = Path(CORE.build_path) / "rust"
    _LOGGER.info("Compiling Rust migration project in %s...", build_dir)

    # Run cargo build
    # In a real environment, we'd need to make sure the rust toolchain is set up for xtensa
    import subprocess

    try:
        rc = subprocess.call(["cargo", "build", "--release"], cwd=build_dir)
        if rc != 0:
            _LOGGER.error("Cargo build failed with return code %d", rc)
            return rc
    except Exception as e:
        _LOGGER.error("Failed to run cargo: %s", e)
        return 1

    _LOGGER.info("Rust migration project compiled successfully.")
    return 0
