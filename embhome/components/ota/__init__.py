"""
OTA component code generation for Rust.

This module provides code generation hooks for the OTA (Over-The-Air update)
component, allowing it to inject dependencies and task spawning code into
generated projects.
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


class OtaComponent(RustComponent):
    """OTA component code generation"""

    def __init__(self):
        super().__init__("ota")

    def get_dependencies(self, gen, config: RustComponentConfig) -> list:
        """Add OTA-specific dependencies"""
        from esphome.rust_generator import RustDependency

        rust_root = config.rust_root

        return [
            RustDependency(
                "esphome-ota", "0.1.0", path=str(rust_root / "components/ota")
            ),
        ]

    def add_spawn_code(self, gen, config: RustComponentConfig) -> None:
        """Spawn OTA server task"""
        gen.add_component_spawn(
            "spawner.spawn(esphome_ota::ota_server(stack)).unwrap();"
        )


# Register the component
register_rust_component("ota", OtaComponent())
