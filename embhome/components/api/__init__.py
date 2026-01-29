"""
API component code generation for Rust.

This module provides code generation hooks for the native API component,
allowing it to inject dependencies and task spawning code into generated projects.
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


class ApiComponent(RustComponent):
    """API component code generation"""

    def __init__(self):
        super().__init__("api")

    def get_dependencies(self, gen, config: RustComponentConfig) -> list:
        """Add API-specific dependencies"""
        from esphome.rust_generator import RustDependency

        rust_root = config.rust_root

        return [
            RustDependency(
                "esphome-api", "0.1.0", path=str(rust_root / "components/api")
            ),
            RustDependency(
                "prost", "0.14.3", default_features=False, features=["alloc"]
            ),
        ]

    def add_spawn_code(self, gen, config: RustComponentConfig) -> None:
        """Spawn API server task"""
        gen.add_component_spawn(
            "spawner.spawn(esphome_api::api_server(stack)).unwrap();"
        )


# Register the component
register_rust_component("api", ApiComponent())
