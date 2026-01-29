import logging
import os
from pathlib import Path
import shutil
import subprocess

from esphome.config import iter_component_configs
from esphome.const import CONF_ID, CONF_PLATFORM, CONF_VARIANT
from esphome.core import CORE
from esphome.helpers import indent, write_file_if_changed

_LOGGER = logging.getLogger(__name__)

# List of components that have native Rust implementations
NATIVE_COMPONENTS = {
    "gpio_switch": "GpioSwitch",
    "gpio_binary_sensor": "GpioBinarySensor",
}

# Mapping of ESPHome variants to Rust Target Triples, Feature Flags, and Toolchain prefixes
VARIANT_MAP = {
    "esp32": {
        "target": "xtensa-esp32-none-elf",
        "feature": "esp32",
        "toolchain": "xtensa-esp32-elf",
        "blob_folder": "esp32",
    },
    "esp32s2": {
        "target": "xtensa-esp32s2-none-elf",
        "feature": "esp32s2",
        "toolchain": "xtensa-esp32s2-elf",
        "blob_folder": "esp32s2",
    },
    "esp32s3": {
        "target": "xtensa-esp32s3-none-elf",
        "feature": "esp32s3",
        "toolchain": "xtensa-esp32s3-elf",
        "blob_folder": "esp32s3",
    },
    "esp32c3": {
        "target": "riscv32imc-unknown-none-elf",
        "feature": "esp32c3",
        "toolchain": "riscv32-esp-elf",
        "blob_folder": "esp32c3",
    },
    "esp32c6": {
        "target": "riscv32imac-unknown-none-elf",
        "feature": "esp32c6",
        "toolchain": "riscv32-esp-elf",
        "blob_folder": "esp32c6",
    },
    "esp32h2": {
        "target": "riscv32imac-unknown-none-elf",
        "feature": "esp32h2",
        "toolchain": "riscv32-esp-elf",
        "blob_folder": "esp32h2",
    },
}


def get_variant_info(config):
    if "esp32" in config:
        variant = config["esp32"].get(CONF_VARIANT)
        if variant:
            variant = variant.lower()
            if variant in VARIANT_MAP:
                return VARIANT_MAP[variant]
    _LOGGER.warning(
        "Could not determine ESP32 variant from config, defaulting to generic esp32"
    )
    return VARIANT_MAP["esp32"]


def find_toolchain_path(toolchain_prefix):
    compiler_name = f"{toolchain_prefix}-g++"
    if shutil.which(compiler_name):
        return None

    pio_packages = Path(os.path.expanduser("~/.platformio/packages"))
    if "riscv32" in toolchain_prefix:
        search_pattern = "toolchain-riscv32-esp*"
    elif "xtensa" in toolchain_prefix:
        arch = toolchain_prefix.split("-")[1]
        search_pattern = f"toolchain-xtensa-{arch}*"
    else:
        search_pattern = "toolchain-*"

    potential_paths = list(pio_packages.glob(search_pattern))
    for p in potential_paths:
        bin_dir = p / "bin"
        if (bin_dir / compiler_name).exists() or (
            bin_dir / f"{compiler_name}.exe"
        ).exists():
            _LOGGER.info("Found toolchain at %s", bin_dir)
            return bin_dir

    _LOGGER.warning(
        "Could not locate toolchain for %s. Compilation may fail if not in PATH.",
        compiler_name,
    )
    return None


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
    old_main = CORE.main_statements
    old_global = CORE.global_statements
    old_component_ids = CORE.component_ids.copy()
    CORE.main_statements = []
    CORE.global_statements = []

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
        await component.to_code(conf)
    finally:
        CORE.register_variable = old_register
        cpp_helpers.register_component = old_register_component
        cg_module.register_component = old_cg_register_component

    setup_code = CORE.cpp_main_section
    global_code = CORE.cpp_global_section

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
    code.append("using namespace esphome;")
    code.append("")

    rust_decls = []
    for comp_id, info in native_info.items():
        if info["platform"] == "gpio_switch":
            rust_decls.append(f"void rust_set_{comp_id}_state(bool state);")

    if rust_decls:
        code.append('extern "C" {')
        code.extend([f"    {decl}" for decl in rust_decls])
        code.append("}")
        code.append("")

    for comp_id, info in native_info.items():
        if info["platform"] == "gpio_switch":
            code.append(f"class {comp_id}Proxy : public switch_::Switch {{")
            code.append(" public:")
            code.append("  void write_state(bool state) override {")
            code.append(f"    rust_set_{comp_id}_state(state);")
            code.append("  }")
            code.append("  std::atomic<bool> shadow_state{false};")
            code.append("};")
            code.append(f"{comp_id}Proxy* {comp_id}_proxy = new {comp_id}Proxy();")
        elif info["platform"] == "gpio_binary_sensor":
            code.append(f"class {comp_id}Proxy : public binary_sensor::BinarySensor {{")
            code.append(" public:")
            code.append("  std::atomic<bool> shadow_state{false};")
            code.append("};")
            code.append(f"{comp_id}Proxy* {comp_id}_proxy = new {comp_id}Proxy();")
    code.append("")

    for comp_id, info in legacy_info.items():
        code.append(f"// Globals for {comp_id}")
        code.append(info["global_code"])

    code.append('extern "C" {')
    code.append("")
    code.append("void call_component_loop(void* component_ptr) {")
    code.append("    auto* component = static_cast<Component*>(component_ptr);")
    code.append("    component->loop();")
    code.append("}")
    code.append("")
    code.append("void call_component_setup(void* component_ptr) {")
    code.append("    auto* component = static_cast<Component*>(component_ptr);")
    code.append("    component->setup();")
    code.append("}")
    code.append("")

    for comp_id, info in legacy_info.items():
        code.append(f"void* create_{comp_id}() {{")
        code.append("    [&]() {")
        code.append(indent(info["setup_code"]))
        code.append("    }();")
        code.append(f"    return static_cast<void*>({comp_id});")
        code.append("}")
        code.append("")

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
    code.append("#![allow(dead_code)]")
    code.append("#![allow(unused_imports)]")
    code.append("")
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

    code.extend(
        [
            f'extern "C" {{ pub fn update_shadow_{comp_id}(state: bool); }}'
            for comp_id in native_info
        ]
    )

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


def generate_cargo_toml(name, feature):
    return f"""
[package]
name = "{name}"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "{name}"
path = "main.rs"

[dependencies]
embassy-executor = {{ version = "0.9.1", features = ["executor-thread"] }}
embassy-time = {{ version = "0.5.0", features = ["generic-queue-8"] }}
embassy-sync = "0.7.2"
embassy-futures = "0.1.1"
embedded-hal = "1.0"
embedded-hal-async = "1.0"

esp-backtrace = {{ version = "0.18.1", features = ["{feature}", "panic-handler", "println"] }}
esp-bootloader-esp-idf = {{ version = "0.4.0", features = ["{feature}", "log-04"] }}
esp-hal = {{ version = "1.0.0", features = ["{feature}", "unstable"] }}
esp-rtos = {{ version = "0.2.0", features = ["{feature}", "embassy", "log-04"] }}
esp-println = {{ version = "0.16.1", features = ["{feature}", "log-04"] }}

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


def generate_cargo_config(target_triple, toolchain_path, toolchain_prefix):
    linker_line = ""
    if toolchain_path:
        linker = toolchain_path / f"{toolchain_prefix}-g++"
        linker_line = f'linker = "{linker}"'
    else:
        linker_line = f'linker = "{toolchain_prefix}-g++"'

    # Fix for multiple definitions (e.g. rtc_clk, stack_chk) between Rust and IDF archives
    flags = [
        "-C",
        "link-arg=-Tlinkall.x",
        "-C",
        "link-arg=-nostartfiles",
        "-C",
        "link-arg=-Wl,-z,muldefs",
    ]

    rustflags_str = ", ".join([f'"{f}"' for f in flags])

    return f"""
[build]
target = "{target_triple}"

[target.{target_triple}]
{linker_line}
runner = "espflash flash --monitor"
rustflags = [
  {rustflags_str}
]
"""


def generate_build_rs():
    # Keep the --start-group fix for circular dependencies
    return """
use std::env;
use std::path::PathBuf;
use std::fs;

fn main() {
    let manifest_dir = env::var("CARGO_MANIFEST_DIR").unwrap();
    let libs_dir = PathBuf::from(manifest_dir).join("libs");

    println!("cargo:rustc-link-search=native={}", libs_dir.display());

    // 1. Start the linker group
    println!("cargo:rustc-link-arg=-Wl,--start-group");

    // 2. Link libesphome.a (Application code)
    println!("cargo:rustc-link-arg=-Wl,--whole-archive");
    println!("cargo:rustc-link-arg=-lesphome");
    println!("cargo:rustc-link-arg=-Wl,--no-whole-archive");

    // 3. Link all framework libraries found in libs/
    if let Ok(entries) = fs::read_dir(&libs_dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if let Some(ext) = path.extension() {
                if ext == "a" {
                    if let Some(stem) = path.file_stem() {
                        let name = stem.to_string_lossy();
                        // Skip libesphome (already linked) and libmain (conflicts)
                        if name.starts_with("lib") && name != "libesphome" && name != "libmain" {
                            println!("cargo:rustc-link-lib=static={}", &name[3..]);
                        }
                    }
                }
            }
        }
    }

    // 4. Link Standard C/C++ Libraries (System)
    println!("cargo:rustc-link-lib=static=stdc++");
    println!("cargo:rustc-link-lib=static=c");
    println!("cargo:rustc-link-lib=static=m");
    println!("cargo:rustc-link-lib=static=gcc");

    // 5. End the linker group
    println!("cargo:rustc-link-arg=-Wl,--end-group");
}
"""


def has_i2c(config):
    return "i2c" in config


def generate_main_rs(config, legacy_info, native_info):
    code = []
    code.append("#![no_std]")
    code.append("#![no_main]")
    code.append("#![allow(unused_imports)]")
    code.append("#![allow(unused_variables)]")
    code.append("")
    code.append("use core::ffi::c_void;")
    code.append("use static_cell::StaticCell;")
    code.append("use embassy_executor::Spawner;")
    code.append("use esp_backtrace as _;")
    code.append("use esp_hal::{")
    code.append("    timer::timg::TimerGroup,")
    code.append("    interrupt::software::SoftwareInterruptControl,")
    code.append("    gpio::{Input, InputConfig, Output, OutputConfig, Pull, Level},")
    code.append("    main,")
    code.append("};")
    code.append("")
    code.append("mod bridge;")
    code.append("mod legacy_wrapper;")
    code.append("mod component_shims;")
    code.append("mod components;")
    code.append("")
    code.append("use legacy_wrapper::LegacyWrapper;")
    code.append("")
    code.append("#[esp_rtos::main]")
    code.append("async fn main(spawner: Spawner) {")
    code.append("    let config = esp_hal::Config::default();")
    code.append("    let peripherals = esp_hal::init(config);")
    code.append("")
    code.append(
        "    let sw_int = SoftwareInterruptControl::new(peripherals.SW_INTERRUPT);"
    )
    code.append("    let timg0 = TimerGroup::new(peripherals.TIMG0);")
    code.append("    esp_rtos::start(timg0.timer0, sw_int.software_interrupt0);")
    code.append("")

    if has_i2c(config):
        i2c_configs = config["i2c"]
        if not isinstance(i2c_configs, list):
            i2c_configs = [i2c_configs]

        for i, i2c_conf in enumerate(i2c_configs):
            sda_pin = i2c_conf.get("sda", 21)
            scl_pin = i2c_conf.get("scl", 22)
            freq = str(i2c_conf.get("frequency", "100kHz")).lower().replace("khz", "")

            code.append(f"    // Initialize I2C bus {i}")
            periph = f"I2C{i}"
            code.append(f"    let i2c{i} = esp_hal::i2c::master::I2c::new(")
            code.append(f"        peripherals.{periph},")
            code.append("        esp_hal::i2c::master::Config::default()")
            code.append(
                f"            .with_frequency(esp_hal::time::Rate::from_khz({freq}))"
            )
            code.append("    )")
            code.append(f"    .with_sda(peripherals.GPIO{sda_pin})")
            code.append(f"    .with_scl(peripherals.GPIO{scl_pin})")
            code.append("    .into_async();")

            if i == 0:
                code.append(f"    let async_i2c = bridge::AsyncI2cBus::new(i2c{i});")
                code.append("    unsafe { bridge::I2C_BUS = Some(async_i2c); }")
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
        count = len(legacy_ptrs)
        code.append(
            f"    static LEGACY_ARRAY: StaticCell<[(&str, *mut c_void); {count}]> = StaticCell::new();"
        )
        code.append("    let legacy_array = LEGACY_ARRAY.init([")
        code.extend([f"        {ptr}," for ptr in legacy_ptrs])
        code.append("    ]);")
        code.append("    unsafe { bridge::LEGACY_COMPONENTS = legacy_array; }")

    for comp_id, info in native_info.items():
        if info["platform"] == "gpio_switch":
            pin = info["conf"].get("pin", 0)
            code.append(f"    // Config for {comp_id}")
            code.append("    let config = OutputConfig::default();")
            code.append(
                f"    let pin = Output::new(peripherals.GPIO{pin}, Level::Low, config);"
            )
            code.append(
                f"    let mut {comp_id} = crate::components::gpio_switch::GpioSwitch::new("
            )
            code.append(f'        "{comp_id}", pin,')
            code.append(
                f"        &bridge::{comp_id.upper()}_CMD, bridge::update_shadow_{comp_id}"
            )
            code.append("    );")
            code.append(f"    spawner.spawn(run_{comp_id}({comp_id})).unwrap();")

        elif info["platform"] == "gpio_binary_sensor":
            pin = info["conf"].get("pin", 0)
            code.append(f"    // Config for {comp_id}")
            code.append("    let config = InputConfig::default().with_pull(Pull::Up);")
            code.append(f"    let pin = Input::new(peripherals.GPIO{pin}, config);")
            code.append(
                f"    let mut {comp_id} = crate::components::gpio_binary_sensor::GpioBinarySensor::new("
            )
            code.append(f'        "{comp_id}", pin,')
            code.append(f"        bridge::update_shadow_{comp_id}")
            code.append("    );")
            code.append(f"    spawner.spawn(run_{comp_id}({comp_id})).unwrap();")

    code.append("}")
    code.append("")

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

    code.append("#[embassy_executor::task]")
    code.append("async fn run_legacy_component(mut wrapper: LegacyWrapper) {")
    code.append("    wrapper.run().await;")
    code.append("}")

    return "\n".join(code)


def generate_i2c_bridge_rs():
    return """
#![allow(dead_code)]
#![allow(unused_imports)]
use core::slice;
use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;
use embassy_sync::mutex::Mutex;
use esp_hal::i2c::master::I2c;
use esp_hal::Async;
use embedded_hal_async::i2c::I2c as I2cTrait;

pub struct AsyncI2cBus {
    bus: Mutex<CriticalSectionRawMutex, I2c<'static, Async>>,
}

impl AsyncI2cBus {
    pub fn new(i2c: I2c<'static, Async>) -> Self {
        Self {
            bus: Mutex::new(i2c),
        }
    }

    pub async fn write(&self, addr: u8, bytes: &[u8]) -> Result<(), esp_hal::i2c::master::Error> {
        let mut bus = self.bus.lock().await;
        bus.write(addr, bytes)
    }

    pub async fn read(&self, addr: u8, buffer: &mut [u8]) -> Result<(), esp_hal::i2c::master::Error> {
        let mut bus = self.bus.lock().await;
        bus.read(addr, buffer)
    }

    pub async fn write_read(
        &self,
        addr: u8,
        bytes: &[u8],
        buffer: &mut [u8]
    ) -> Result<(), esp_hal::i2c::master::Error> {
        let mut bus = self.bus.lock().await;
        bus.write_read(addr, bytes, buffer)
    }
}

pub static mut I2C_BUS: Option<AsyncI2cBus> = None;

#[no_mangle]
pub extern "C" fn rust_i2c_write(
    addr: u8,
    data: *const u8,
    len: usize
) -> i32 {
    if data.is_null() || len == 0 { return -1; }
    let bytes = unsafe { slice::from_raw_parts(data, len) };

    embassy_futures::block_on(async {
        #[allow(static_mut_refs)]
        let bus = unsafe { I2C_BUS.as_mut().expect("I2C not initialized") };
        match bus.write(addr, bytes).await {
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
    if buffer.is_null() || len == 0 { return -1; }
    let buffer_slice = unsafe { slice::from_raw_parts_mut(buffer, len) };

    embassy_futures::block_on(async {
        #[allow(static_mut_refs)]
        let bus = unsafe { I2C_BUS.as_mut().expect("I2C not initialized") };
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

    embassy_futures::block_on(async {
        #[allow(static_mut_refs)]
        let bus = unsafe { I2C_BUS.as_mut().expect("I2C not initialized") };
        match bus.write_read(addr, write_bytes, read_slice).await {
            Ok(()) => 0,
            Err(_) => -1,
        }
    })
}
"""


def generate_gpio_switch_rs():
    return """
#![allow(dead_code)]
use esp_hal::gpio::Output;
use embassy_sync::channel::Channel;
use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;

#[repr(C)]
#[derive(Clone, Copy)]
pub enum SwitchCommand {
    TurnOn,
    TurnOff,
    Toggle,
}

pub struct GpioSwitch {
    id: &'static str,
    pin: Output<'static>,
    command_channel: &'static Channel<CriticalSectionRawMutex, SwitchCommand, 8>,
    on_update: fn(bool),
}

impl GpioSwitch {
    pub fn new(
        id: &'static str,
        pin: Output<'static>,
        command_channel: &'static Channel<CriticalSectionRawMutex, SwitchCommand, 8>,
        on_update: fn(bool)
    ) -> Self {
        Self {
            id,
            pin,
            command_channel,
            on_update,
        }
    }

    pub async fn run(&mut self) {
        loop {
            let cmd = self.command_channel.receive().await;
            match cmd {
                SwitchCommand::TurnOn => self.pin.set_high(),
                SwitchCommand::TurnOff => self.pin.set_low(),
                SwitchCommand::Toggle => self.pin.toggle(),
            }
            self.update_shadow();
        }
    }

    fn update_shadow(&self) {
        let is_on = self.pin.is_set_high();
        (self.on_update)(is_on);
    }
}
"""


def generate_gpio_binary_sensor_rs():
    return """
#![allow(dead_code)]
use esp_hal::gpio::Input;
use embassy_time::{Duration, Timer};

pub struct GpioBinarySensor {
    id: &'static str,
    pin: Input<'static>,
    last_state: bool,
    on_update: fn(bool),
}

impl GpioBinarySensor {
    pub fn new(id: &'static str, pin: Input<'static>, on_update: fn(bool)) -> Self {
        Self {
            id,
            pin,
            last_state: false,
            on_update,
        }
    }

    pub async fn run(&mut self) {
        self.last_state = self.pin.is_high();
        self.update_shadow(self.last_state);

        loop {
            let current_state = self.pin.is_high();
            if current_state != self.last_state {
                self.last_state = current_state;
                self.update_shadow(current_state);
            }
            Timer::after(Duration::from_millis(50)).await;
        }
    }

    fn update_shadow(&self, state: bool) {
        (self.on_update)(state);
    }
}
"""


def build_cpp_lib(build_dir, toolchain_path, toolchain_prefix, blob_folder):
    _LOGGER.info("Starting C++ compilation via PlatformIO...")
    esphome_build_dir = build_dir.parent
    subprocess.call(["pio", "run"], cwd=esphome_build_dir)

    pio_dir = esphome_build_dir / ".pio" / "build"
    libs_dir = build_dir / "libs"
    if libs_dir.exists():
        shutil.rmtree(libs_dir)
    libs_dir.mkdir()

    env_dir = None
    if pio_dir.exists():
        for d in pio_dir.iterdir():
            if d.is_dir() and d.name != "project.checksum":
                env_dir = d
                break

    if not env_dir:
        _LOGGER.error("Could not find PlatformIO build environment in %s", pio_dir)
        return False

    obj_files = []
    src_build_dir = env_dir / "src"
    if src_build_dir.exists():
        for root, dirs, files in os.walk(src_build_dir):
            obj_files.extend(
                [os.path.join(root, file) for file in files if file.endswith(".o")]
            )

    if not obj_files:
        _LOGGER.error("No object files found in %s", src_build_dir)
        for root, dirs, files in os.walk(env_dir):
            obj_files.extend(
                [
                    os.path.join(root, file)
                    for file in files
                    if file.endswith(".o") and "framework-espidf" not in root
                ]
            )

    if not obj_files:
        _LOGGER.error("Fatal: No application object files found to archive.")
        return False

    ar_tool = "ar"
    if toolchain_path:
        ar_tool = toolchain_path / f"{toolchain_prefix}-ar"

    libesphome_path = libs_dir / "libesphome.a"
    try:
        subprocess.check_call([str(ar_tool), "rcs", str(libesphome_path)] + obj_files)
        _LOGGER.info("Created %s with %d objects", libesphome_path, len(obj_files))
    except Exception as e:
        _LOGGER.error("Failed to archive libesphome.a: %s", e)
        return False

    _LOGGER.info("Gathering static libraries...")
    for root, dirs, files in os.walk(env_dir):
        for file in files:
            if file.endswith(".a") and file != "libesphome.a":
                shutil.copy(Path(root) / file, libs_dir / file)

    home = Path.home()
    framework_dir = home / ".platformio" / "packages" / "framework-espidf"

    if framework_dir.exists():
        _LOGGER.info(
            "Searching framework-espidf for precompiled blobs (folder: %s)...",
            blob_folder,
        )
        found_blobs = 0
        for root, dirs, files in os.walk(framework_dir):
            if Path(root).name == blob_folder or Path(root).name == "lib":
                for file in files:
                    if file.endswith(".a"):
                        src = Path(root) / file
                        dst = libs_dir / file
                        if not dst.exists():
                            shutil.copy(src, dst)
                            found_blobs += 1
        _LOGGER.info("Found and copied %d binary blobs.", found_blobs)
    else:
        _LOGGER.warning(
            "ESP-IDF framework not found at %s. Linker errors likely.", framework_dir
        )

    return True


async def generate(config):
    _LOGGER.info("Generating Rust migration bridge...")

    variant_info = get_variant_info(config)
    target_triple = variant_info["target"]
    rust_feature = variant_info["feature"]
    toolchain_prefix = variant_info["toolchain"]

    _LOGGER.info(
        "Detected variant: %s, feature: %s, target: %s",
        config.get("esp32", {}).get(CONF_VARIANT, "unknown"),
        rust_feature,
        target_triple,
    )

    toolchain_path = find_toolchain_path(toolchain_prefix)

    legacy, native = classify_components(config)

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

    native_info = {}
    for domain, component, conf in native:
        comp_id = conf.get(CONF_ID)
        if comp_id:
            native_info[str(comp_id)] = {
                "platform": conf.get(CONF_PLATFORM),
                "conf": conf,
            }

    build_dir = Path(CORE.build_path) / "rust"
    build_dir.mkdir(parents=True, exist_ok=True)

    src_dir = Path(CORE.build_path) / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    write_file_if_changed(
        src_dir / "bridge.cpp", generate_bridge_cpp(legacy_info, native_info)
    )
    write_file_if_changed(
        build_dir / "bridge.h",
        '#include "esphome.h"\nextern "C" {\nvoid call_component_loop(void* ptr);\nvoid call_component_setup(void* ptr);\n}\n',
    )
    write_file_if_changed(
        build_dir / "bridge.rs", generate_bridge_rs(legacy_info, native_info)
    )
    write_file_if_changed(
        build_dir / "main.rs", generate_main_rs(config, legacy_info, native_info)
    )
    write_file_if_changed(
        build_dir / "Cargo.toml", generate_cargo_toml(CORE.name, rust_feature)
    )
    write_file_if_changed(build_dir / "build.rs", generate_build_rs())

    cargo_config_dir = build_dir / ".cargo"
    cargo_config_dir.mkdir(exist_ok=True)
    write_file_if_changed(
        cargo_config_dir / "config.toml",
        generate_cargo_config(target_triple, toolchain_path, toolchain_prefix),
    )

    embhome_dir = Path("embhome")
    if (embhome_dir / "legacy_wrapper.rs").exists():
        shutil.copy(embhome_dir / "legacy_wrapper.rs", build_dir / "legacy_wrapper.rs")

    shims_dir = build_dir / "component_shims"
    shims_dir.mkdir(exist_ok=True)
    write_file_if_changed(shims_dir / "i2c_bridge.rs", generate_i2c_bridge_rs())
    write_file_if_changed(shims_dir / "mod.rs", "pub mod i2c_bridge;\n")

    if (embhome_dir / "component_shims" / "i2c_shim.cpp").exists():
        shutil.copy(
            embhome_dir / "component_shims" / "i2c_shim.cpp", src_dir / "i2c_shim.cpp"
        )

    comp_dir = build_dir / "components"
    comp_dir.mkdir(exist_ok=True)
    write_file_if_changed(comp_dir / "gpio_switch.rs", generate_gpio_switch_rs())
    write_file_if_changed(
        comp_dir / "gpio_binary_sensor.rs", generate_gpio_binary_sensor_rs()
    )
    write_file_if_changed(
        comp_dir / "mod.rs", "pub mod gpio_switch;\npub mod gpio_binary_sensor;\n"
    )

    _LOGGER.info("Rust migration project generated in %s", build_dir)


def compile(config):
    build_dir = Path(CORE.build_path) / "rust"
    _LOGGER.info("Compiling Rust migration project in %s...", build_dir)

    variant_info = get_variant_info(config)
    toolchain_prefix = variant_info["toolchain"]
    blob_folder = variant_info["blob_folder"]
    toolchain_path = find_toolchain_path(toolchain_prefix)

    if not build_cpp_lib(build_dir, toolchain_path, toolchain_prefix, blob_folder):
        _LOGGER.error("Failed to build C++ library. Aborting Rust compilation.")
        return 1

    # Removed logic that automatically includes PlatformIO linker scripts
    # to avoid "redefinition of memory region" errors.

    log_file = build_dir / "cargo_build.log"
    try:
        with open(log_file, "w") as f:
            _LOGGER.info("Writing Cargo output to %s", log_file)
            rc = subprocess.call(
                ["cargo", "build", "--release"],
                cwd=build_dir,
                stdout=f,
                stderr=subprocess.STDOUT,
            )

        if rc != 0:
            _LOGGER.error(
                "Cargo build failed with return code %d. See %s for details.",
                rc,
                log_file,
            )
            return rc
    except Exception as e:
        _LOGGER.error("Failed to run cargo: %s", e)
        return 1

    _LOGGER.info("Rust migration project compiled successfully.")
    return 0
