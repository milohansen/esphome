"""
Rust code generation for ESPHome.

This module generates Rust projects from ESPHome YAML configurations.
It uses a component-based architecture where each component (WiFi, API, GPIO, etc.)
provides its own code generation hooks.
"""

import os
from pathlib import Path
import sys

from esphome.const import CONF_NAME
from esphome.rust_generator import RustDependency, RustGenerator

# Add embhome to path for component imports
embhome_path = Path(os.getcwd()) / "embhome"
if str(embhome_path) not in sys.path:
    sys.path.insert(0, str(embhome_path))

# Import component system
import embhome.components.api  # noqa: F401, E402
import embhome.components.gpio  # noqa: F401, E402
import embhome.components.ota  # noqa: F401, E402
import embhome.components.sensor  # noqa: F401, E402

# Import all components to trigger registration
# These imports have side effects - they register components
import embhome.components.wifi  # noqa: F401, E402
from embhome.core.rust_component import (  # noqa: E402
    RustComponentConfig,
    get_rust_component,
)


def generate_rust_project(config, output_dir: Path):
    """
    Generate a Rust project from ESPHome configuration.

    Args:
        config: Parsed ESPHome YAML configuration
        output_dir: Directory to write generated files
    """
    gen = RustGenerator()

    # Determine chip/features
    chip = "esp32"
    board = config["esphome"].get("board", "esp32")
    board_parts = board.split("-")
    if (
        board_parts[0] == "esp32"
        and len(board_parts) > 1
        and board_parts[1] in ["c3", "s2", "s3", "c2", "c6", "h2"]
    ):
        chip = f"esp32{board_parts[1]}"

    # Paths
    rust_root = Path(os.getcwd()) / "embhome"

    # Create component configuration
    component_config = RustComponentConfig(
        chip=chip, config=config, rust_root=rust_root
    )

    # ============================================================
    # Phase 0: Core Dependencies (always present)
    # ============================================================
    gen.add_dependency(
        RustDependency("esphome-core", "0.1.0", path=str(rust_root / "core"))
    )
    gen.add_dependency(
        RustDependency("esphome-hal", "0.1.0", path=str(rust_root / "hal"))
    )
    gen.add_dependency(
        RustDependency("esphome-config", "0.1.0", path=str(rust_root / "config"))
    )

    # Platform HAL Dependencies
    gen.add_dependency(
        RustDependency("esp-hal", "1.0", features=[chip, "log-04", "psram", "unstable"])
    )
    gen.add_dependency(RustDependency("esp-alloc", "0.9", features=[chip]))
    gen.add_dependency(
        RustDependency(
            "esp-rtos",
            "0.2.0",
            features=[chip, "embassy", "log-04", "esp-alloc", "esp-radio"],
        )
    )
    gen.add_dependency(
        RustDependency("embassy-executor", "0.9.1", features=["executor-thread", "log"])
    )
    gen.add_dependency(RustDependency("log", "0.4"))
    gen.add_dependency(
        RustDependency(
            "esp-backtrace", "0.14.2", features=[chip, "panic-handler", "println"]
        )
    )
    gen.add_dependency(RustDependency("static_cell", "2.1.0"))

    # ============================================================
    # Phase 1: Component Dependencies
    # ============================================================
    # Order matters: wifi must come before api/ota since they depend on stack
    component_order = [
        "wifi",
        "api",
        "ota",
        "gpio",
        "sensor",
        "binary_sensor",
        "switch",
    ]

    for component_name in component_order:
        if component_name in config:
            component = get_rust_component(component_name)
            if component:
                deps = component.get_dependencies(gen, component_config)
                for dep in deps:
                    # Check for duplicates before adding
                    if dep.name not in [d.name for d in gen.dependencies]:
                        gen.add_dependency(dep)

    # ============================================================
    # Phase 2: Global Code (heap allocator, statics, etc.)
    # ============================================================
    for component_name in component_order:
        if component_name in config:
            component = get_rust_component(component_name)
            if component:
                component.add_global_code(gen, component_config)

    # ============================================================
    # Phase 3: App Initialization (core, always present)
    # ============================================================
    app_name = config["esphome"][CONF_NAME]

    gen.add_main_code(
        f'let mut app = Application::new("{app_name}", Platform::{chip.capitalize()});'
    )
    gen.add_main_code('app.init().await.expect("App init failed");')
    gen.add_main_code(
        "let io = esp_hal::gpio::IO::new(peripherals.GPIO, peripherals.IO_MUX);"
    )

    # ============================================================
    # Phase 4: Component Setup Code
    # ============================================================
    for component_name in component_order:
        if component_name in config:
            component = get_rust_component(component_name)
            if component:
                component.add_setup_code(gen, component_config)

    # ============================================================
    # Phase 5: Spawn Component Tasks
    # ============================================================
    for component_name in component_order:
        if component_name in config:
            component = get_rust_component(component_name)
            if component:
                component.add_spawn_code(gen, component_config)

    # ============================================================
    # Write Output Files
    # ============================================================
    src_dir = output_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    # Write Cargo.toml
    with open(output_dir / "Cargo.toml", "w") as f:
        f.write(gen.generate_cargo_toml())

    # Write main.rs
    with open(src_dir / "main.rs", "w") as f:
        f.write(gen.generate_main_rs())

    # Write .cargo/config.toml
    cargo_conf_dir = output_dir / ".cargo"
    cargo_conf_dir.mkdir(exist_ok=True)

    # Determine target triple
    target_map = {
        "esp32": "xtensa-esp32-none-elf",
        "esp32s2": "xtensa-esp32s2-none-elf",
        "esp32s3": "xtensa-esp32s3-none-elf",
        "esp32c2": "riscv32imc-unknown-none-elf",
        "esp32c3": "riscv32imc-unknown-none-elf",
        "esp32c6": "riscv32imac-unknown-none-elf",
        "esp32h2": "riscv32imac-unknown-none-elf",
    }
    target = target_map.get(chip, "xtensa-esp32-none-elf")

    with open(cargo_conf_dir / "config.toml", "w") as f:
        f.write(
            f"[build]\n"
            f'target = "{target}"\n\n'
            f"[target.{target}]\n"
            f'runner = "espflash flash --monitor"\n'
        )


# ============================================================
# Deprecated Helper Functions (kept for backward compatibility)
# ============================================================
# These functions are no longer used by generate_rust_project()
# but are kept in case external code references them.
# They will be removed in a future version.
# ============================================================


def get_pin_number(pin_config):
    """
    DEPRECATED: Extract pin number from config.
    Use GpioComponent._get_pin_number() instead.
    """
    if isinstance(pin_config, dict):
        return pin_config.get("number")
    return pin_config


def generate_gpio_switch(gen: RustGenerator, config, index):
    """
    DEPRECATED: Generate GPIO switch code.
    Use GpioComponent instead.
    """
    # This function is no longer called by generate_rust_project()
    # It's kept for backward compatibility only
    pass


def generate_gpio_binary_sensor(gen: RustGenerator, config, index):
    """
    DEPRECATED: Generate GPIO binary sensor code.
    Use GpioComponent instead.
    """
    # This function is no longer called by generate_rust_project()
    # It's kept for backward compatibility only
    pass


def generate_uptime_sensor(gen: RustGenerator, config, index):
    """
    DEPRECATED: Generate uptime sensor code.
    Use SensorComponent instead.
    """
    # This function is no longer called by generate_rust_project()
    # It's kept for backward compatibility only
    pass
