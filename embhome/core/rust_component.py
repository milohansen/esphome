"""
Base class for Rust component code generation.

This module provides the foundation for component-based Rust code generation,
similar to how C++ components work in ESPHome. Each component can register
itself and provide hooks for dependencies, initialization code, and task spawning.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RustComponentConfig:
    """Configuration passed to component during code generation"""

    chip: str
    config: dict[str, Any]
    rust_root: Path


class RustComponent:
    """
    Base class for Rust component code generation.

    Components should subclass this and implement the hooks they need.
    Each hook is optional - only override what your component needs.
    """

    def __init__(self, component_name: str):
        self.component_name = component_name

    def get_dependencies(self, gen: Any, config: RustComponentConfig) -> list[Any]:
        """
        Return list of Rust dependencies this component needs.

        Called early in code generation to build dependency list.

        Args:
            gen: RustGenerator instance
            config: Component configuration

        Returns:
            List of RustDependency objects
        """
        return []

    def add_global_code(self, gen: Any, config: RustComponentConfig) -> None:
        """
        Add global macros, statics, and top-level code.

        Called before main() is generated. Use this for:
        - Heap allocator setup
        - Global static variables
        - Top-level use statements

        Args:
            gen: RustGenerator instance
            config: Component configuration
        """
        pass

    def add_setup_code(self, gen: Any, config: RustComponentConfig) -> None:
        """
        Add code to main() for component initialization.

        Called during main() generation, before component spawning.
        Use this for:
        - Peripheral initialization
        - Resource allocation
        - Configuration setup

        Args:
            gen: RustGenerator instance
            config: Component configuration
        """
        pass

    def add_spawn_code(self, gen: Any, config: RustComponentConfig) -> None:
        """
        Add component task spawning code.

        Called at the end of main() for spawning component tasks.
        Use this for:
        - Spawning embassy tasks
        - Starting component loops

        Args:
            gen: RustGenerator instance
            config: Component configuration
        """
        pass

    def requires_heap(self) -> bool:
        """
        Return True if component needs heap allocator.

        Returns:
            True if heap allocator is required
        """
        return False

    def heap_size(self) -> int:
        """
        Return required heap size in KB.

        Only used if requires_heap() returns True.

        Returns:
            Heap size in kilobytes
        """
        return 0


# Component registry
_RUST_COMPONENTS: dict[str, RustComponent] = {}


def register_rust_component(name: str, component: RustComponent) -> None:
    """
    Register a Rust component for code generation.

    Args:
        name: Component name (matches config key, e.g., "wifi", "api")
        component: RustComponent instance
    """
    _RUST_COMPONENTS[name] = component


def get_rust_component(name: str) -> RustComponent | None:
    """
    Get a registered Rust component.

    Args:
        name: Component name

    Returns:
        RustComponent instance or None if not found
    """
    return _RUST_COMPONENTS.get(name)


def get_all_rust_components() -> dict[str, RustComponent]:
    """
    Get all registered Rust components.

    Returns:
        Dictionary mapping component names to RustComponent instances
    """
    return _RUST_COMPONENTS


def clear_rust_components() -> None:
    """
    Clear all registered components.

    Useful for testing and reloading components.
    """
    _RUST_COMPONENTS.clear()
