"""
GPIO component code generation for Rust.

This module provides code generation hooks for GPIO switches and binary sensors,
allowing them to inject dependencies and generate component tasks.
"""

from pathlib import Path
import sys

# Add embhome to path so we can import rust_component
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from embhome.core.rust_component import (  # noqa: E402
    RustComponent,
    RustComponentConfig,
    register_rust_component,
)


class GpioComponent(RustComponent):
    """GPIO component code generation"""

    def __init__(self):
        super().__init__("gpio")

    def get_dependencies(self, gen, config: RustComponentConfig) -> list:
        """Add GPIO component dependency"""
        from esphome.rust_generator import RustDependency

        rust_root = config.rust_root

        return [
            RustDependency(
                "esphome-gpio", "0.1.0", path=str(rust_root / "components/gpio")
            ),
        ]

    def add_setup_code(self, gen, config: RustComponentConfig) -> None:
        """Generate code for GPIO switches and binary sensors"""
        user_config = config.config

        # Generate GPIO switches
        if "switch" in user_config:
            for i, switch_config in enumerate(user_config["switch"]):
                if switch_config.get("platform") == "gpio":
                    self._generate_switch(gen, switch_config, i)

        # Generate GPIO binary sensors
        if "binary_sensor" in user_config:
            for i, sensor_config in enumerate(user_config["binary_sensor"]):
                if sensor_config.get("platform") == "gpio":
                    self._generate_binary_sensor(gen, sensor_config, i)

    def _generate_switch(self, gen, switch_config: dict, index: int) -> None:
        """Generate code for a GPIO switch"""
        from esphome.rust_generator import RustFunction

        switch_id = switch_config.get("id", f"switch_{index}")
        pin_num = self._get_pin_number(switch_config["pin"])
        inverted = switch_config.get("inverted", False)
        initial_state = False

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
            f"spawner.spawn({task_name}(io.pins.gpio{pin_num}))"
            f'.expect("Failed to spawn {switch_id}");'
        )

    def _generate_binary_sensor(self, gen, sensor_config: dict, index: int) -> None:
        """Generate code for a GPIO binary sensor"""
        from esphome.rust_generator import RustFunction

        sensor_id = sensor_config.get("id", f"binary_sensor_{index}")
        pin_num = self._get_pin_number(sensor_config["pin"])
        inverted = sensor_config.get("inverted", False)
        pullup = sensor_config.get("pullup", False)
        pulldown = sensor_config.get("pulldown", False)

        # Generate task function
        task_name = f"{sensor_id}_task"

        body = f"""
    use embassy_sync::channel::Channel;
    use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;
    use esphome_core::{{Component, ActorAddress}};
    use esphome_gpio::binary_sensor::{{GpioBinarySensor, GpioBinarySensorConfig, BinarySensorEvent}};

    static MAILBOX: Channel<CriticalSectionRawMutex, (), 8> = Channel::new();

    let mut comp = GpioBinarySensor::new("{sensor_id}");
    let config = GpioBinarySensorConfig {{
        pin,
        inverted: {str(inverted).lower()},
        pullup: {str(pullup).lower()},
        pulldown: {str(pulldown).lower()},
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
            f"spawner.spawn({task_name}(io.pins.gpio{pin_num}))"
            f'.expect("Failed to spawn {sensor_id}");'
        )

    def _get_pin_number(self, pin_config):
        """Extract pin number from config"""
        if isinstance(pin_config, dict):
            return pin_config.get("number")
        return pin_config


# Register the component
register_rust_component("gpio", GpioComponent())
