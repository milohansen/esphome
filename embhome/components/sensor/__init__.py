"""
Sensor component code generation for Rust.

This module provides code generation hooks for various sensor types,
currently supporting uptime sensors.
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


class SensorComponent(RustComponent):
    """Sensor component code generation"""

    def __init__(self):
        super().__init__("sensor")

    def get_dependencies(self, gen, config: RustComponentConfig) -> list:
        """Add sensor-specific dependencies based on platforms used"""
        from esphome.rust_generator import RustDependency

        rust_root = config.rust_root
        user_config = config.config
        deps = []

        # Check if uptime sensor is used
        if "sensor" in user_config:
            for sensor_config in user_config["sensor"]:
                if sensor_config.get("platform") == "uptime":
                    deps.extend(
                        [
                            RustDependency(
                                "esphome-uptime",
                                "0.1.0",
                                path=str(rust_root / "components/uptime"),
                            ),
                            RustDependency(
                                "esphome-sensor",
                                "0.1.0",
                                path=str(rust_root / "components/sensor"),
                            ),
                        ]
                    )
                    break  # Only need to add once

        return deps

    def add_setup_code(self, gen, config: RustComponentConfig) -> None:
        """Generate code for sensors"""
        user_config = config.config

        # Generate uptime sensors
        if "sensor" in user_config:
            for i, sensor_config in enumerate(user_config["sensor"]):
                if sensor_config.get("platform") == "uptime":
                    self._generate_uptime_sensor(gen, sensor_config, i)

    def _generate_uptime_sensor(self, gen, sensor_config: dict, index: int) -> None:
        """Generate code for an uptime sensor"""
        from esphome.rust_generator import RustFunction

        sensor_id = sensor_config.get("id", f"uptime_sensor_{index}")
        update_interval = sensor_config.get("update_interval", "60s")

        # Simple duration parsing
        seconds = 60
        if isinstance(update_interval, str) and update_interval.endswith("s"):
            seconds = int(update_interval[:-1])

        task_name = f"{sensor_id}_task"

        body = f"""
    use embassy_sync::channel::Channel;
    use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;
    use embassy_time::Duration;
    use esphome_core::Component;
    use esphome_uptime::UptimeSensor;

    static MAILBOX: Channel<CriticalSectionRawMutex, (), 8> = Channel::new();

    let mut comp = UptimeSensor::new("{sensor_id}");
    comp.setup(Duration::from_secs({seconds})).await.expect("Setup failed");
    comp.run(MAILBOX.receiver()).await;
        """

        func = RustFunction(
            name=task_name,
            body=body,
            is_async=True,
            attributes=["#[embassy_executor::task]"],
        )

        gen.add_function(func)
        gen.add_component_spawn(
            f'spawner.spawn({task_name}()).expect("Failed to spawn {sensor_id}");'
        )


# Register the component
register_rust_component("sensor", SensorComponent())
