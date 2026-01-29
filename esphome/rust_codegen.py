import os
from pathlib import Path

from esphome.const import CONF_NAME, CONF_PLATFORM
from esphome.rust_generator import RustDependency, RustFunction, RustGenerator


def get_pin_number(pin_config):
    # This assumes pin_config has been normalized by standard validation
    if isinstance(pin_config, dict):
        return pin_config.get("number")
    return pin_config


def generate_gpio_switch(gen: RustGenerator, config, index):
    switch_id = config.get("id", f"switch_{index}")
    pin_num = get_pin_number(config["pin"])
    inverted = config.get("inverted", False)
    initial_state = False  # TODO: Get from config

    # Generate task function
    task_name = f"{switch_id}_task"

    body = f"""
    use embassy_sync::channel::Channel;
    use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;
    use esphome_core::{{Component, ActorAddress}};
    use esphome_gpio::switch::{{GpioSwitch, GpioSwitchConfig, SwitchCommand}};

    static MAILBOX: Channel<CriticalSectionRawMutex, SwitchCommand, 8> = Channel::new();

    let mut comp = GpioSwitch::new("{switch_id}");
    let config = GpioSwitchConfig {{
        pin,
        initial_state: {str(initial_state).lower()},
        inverted: {str(inverted).lower()},
    }};

    comp.setup(config).await.expect("Setup failed");
    comp.run(MAILBOX.receiver()).await;
    """

    func = RustFunction(
        name=task_name,
        body=body,
        is_async=True,
        attributes=["#[embassy_executor::task]"],
        args=[f"pin: esp_hal::gpio::GpioPin<{pin_num}>"],
    )

    gen.add_function(func)

    # Add spawn call to main
    gen.add_component_spawn(
        f'spawner.spawn({task_name}(io.pins.gpio{pin_num})).expect("Failed to spawn {switch_id}");'
    )


def generate_rust_project(config, output_dir: Path):
    gen = RustGenerator()

    # Determine chip/features
    # Simple logic for now, defaulting to esp32
    chip = "esp32"
    if config["esphome"].get("board") in ["esp32-c3-devkitm-1"]:
        chip = "esp32c3"

    # Core Dependencies
    # Paths are relative to the build directory (usually .esphome/build/name)
    # We assume the rust workspace is at repo root
    # Adjust paths to point to the repo root from build dir
    # repo_root = "../../../../esphome/rust"  # Adjust based on depth
    # Actually, we should probably copy the crates or use absolute paths?
    # For dev, absolute path to repo is best.
    rust_root = Path(os.getcwd()) / "esphome/rust"

    gen.add_dependency(
        RustDependency("esphome-core", "0.1.0", path=str(rust_root / "esphome-core"))
    )
    gen.add_dependency(
        RustDependency("esphome-hal", "0.1.0", path=str(rust_root / "esphome-hal"))
    )
    gen.add_dependency(
        RustDependency(
            "esphome-config", "0.1.0", path=str(rust_root / "esphome-config")
        )
    )

    # HAL dependencies
    gen.add_dependency(RustDependency("esp-hal", "0.22.0", features=[chip]))
    gen.add_dependency(
        RustDependency("esp-hal-embassy", "0.5.0", features=[chip, "log"])
    )

    executor_features = ["task-arena-size-32768"]
    if chip == "esp32c3":
        executor_features.append("arch-riscv32")
        executor_features.append("executor-thread")
    else:
        # Default to xtensa for esp32, esp32s2, esp32s3
        executor_features.append("arch-xtensa")
        executor_features.append("executor-thread")

    gen.add_dependency(
        RustDependency("embassy-executor", "0.6.0", features=executor_features)
    )
    gen.add_dependency(RustDependency("log", "0.4"))
    gen.add_dependency(
        RustDependency(
            "esp-backtrace",
            "0.14.2",
            features=[chip, "exception-handler", "panic-handler", "println"],
        )
    )

    # Main setup
    app_name = config["esphome"][CONF_NAME]
    platform_enum = "Esp32"  # Dynamic based on chip
    if chip == "esp32c3":
        platform_enum = "Esp32c3"

    gen.add_main_code(
        f'let mut app = Application::new("{app_name}", Platform::{platform_enum});'
    )
    gen.add_main_code('app.init().await.expect("App init failed");')
    gen.add_main_code(
        "let io = esp_hal::gpio::IO::new(peripherals.GPIO, peripherals.IO_MUX);"
    )

    # Components
    if "switch" in config:
        gen.add_dependency(
            RustDependency(
                "esphome-gpio", "0.1.0", path=str(rust_root / "esphome-gpio")
            )
        )
        for i, conf in enumerate(config["switch"]):
            if conf[CONF_PLATFORM] == "gpio":
                generate_gpio_switch(gen, conf, i)

    # Write Output
    src_dir = output_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "Cargo.toml", "w") as f:
        f.write(gen.generate_cargo_toml())

    with open(src_dir / "main.rs", "w") as f:
        f.write(gen.generate_main_rs())

    # .cargo/config.toml
    cargo_conf_dir = output_dir / ".cargo"
    cargo_conf_dir.mkdir(exist_ok=True)

    target = "xtensa-esp32-none-elf"
    if chip == "esp32c3":
        target = "riscv32imc-unknown-none-elf"

    with open(cargo_conf_dir / "config.toml", "w") as f:
        f.write(
            f'[build]\ntarget = "{target}"\n\n[target.{target}]\nrunner = "espflash flash --monitor"\n'
        )
