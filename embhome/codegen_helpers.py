"""
ESPHome Rust Code Generator - Dependency Management Helpers

This module provides utilities for the Python code generator to:
1. Ensure correct chip feature propagation
2. Generate Cargo.toml files with proper dependencies
3. Validate workspace dependency consistency
4. Integrate with esp-generate for project scaffolding
"""

from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import sys
from typing import Any

import tomli
import tomli_w

# Supported chip targets
SUPPORTED_CHIPS = [
    "esp32",
    "esp32c3",
    "esp32s2",
    "esp32s3",
    "esp32c2",
    "esp32c5",
    "esp32c6",
    "esp32h2",
    "esp32p4",
]

# Components that need chip features forwarded to them
CHIP_DEPENDENT_COMPONENTS = [
    "esphome-core",
    "esphome-hal",
    "esphome-wifi",
    "esphome-ota",
    "esphome-gpio",
]

# Map ESPHome chip names to esp-generate template names
CHIP_TO_TEMPLATE_MCU = {
    "esp32": "esp32",
    "esp32c3": "esp32c3",
    "esp32s2": "esp32s2",
    "esp32s3": "esp32s3",
    "esp32c2": "esp32c2",
    "esp32c5": "esp32c5",
    "esp32c6": "esp32c6",
    "esp32h2": "esp32h2",
    "esp32p4": "esp32p4",
}


@dataclass
class ComponentDependency:
    """Represents a dependency on an embhome component"""

    name: str
    path: str
    needs_chip_feature: bool = False

    def to_toml(self, chip: str) -> dict:
        """Generate Cargo.toml dependency entry"""
        dep: dict[str, Any] = {"path": self.path}
        if self.needs_chip_feature:
            dep["features"] = [chip]
        return dep


@dataclass
class ProjectConfig:
    """Configuration for a generated ESPHome project"""

    name: str
    chip: str
    components: list[str] = field(default_factory=list)
    workspace_path: Path = field(default_factory=lambda: Path("../embhome"))

    def __post_init__(self):
        if self.chip not in SUPPORTED_CHIPS:
            raise ValueError(
                f"Unsupported chip '{self.chip}'. "
                f"Supported chips: {', '.join(SUPPORTED_CHIPS)}"
            )


class DependencyManager:
    """Manages dependencies for generated ESPHome projects"""

    def __init__(self, workspace_path: Path):
        self.workspace_path = Path(workspace_path)
        self.workspace_deps = self._load_workspace_dependencies()

    def _load_workspace_dependencies(self) -> dict:
        """Load workspace dependencies from embhome/Cargo.toml"""
        workspace_toml = self.workspace_path / "Cargo.toml"
        if not workspace_toml.exists():
            raise FileNotFoundError(
                f"Workspace Cargo.toml not found at {workspace_toml}"
            )

        with open(workspace_toml, "rb") as f:
            data = tomli.load(f)

        return data.get("workspace", {}).get("dependencies", {})

    def get_component_dependencies(self, component: str) -> set[str]:
        """Get all dependencies for a component by reading its Cargo.toml"""
        component_path = self.workspace_path / "components" / component
        if not component_path.exists():
            # Try without components/ prefix
            component_path = self.workspace_path / component

        cargo_toml = component_path / "Cargo.toml"
        if not cargo_toml.exists():
            return set()

        with open(cargo_toml, "rb") as f:
            data = tomli.load(f)

        deps = set()
        for dep_name in data.get("dependencies", {}):
            deps.add(dep_name)

        return deps

    def generate_project_with_esp_generate(
        self, config: ProjectConfig, output_path: Path
    ) -> bool:
        """
        Generate project using esp-generate (cargo-generate) as base.

        Returns True if successful, False if cargo-generate not available.
        """
        # Check if cargo-generate is installed
        try:
            subprocess.run(
                ["cargo-generate", "--version"],
                check=True,
                capture_output=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

        # Generate project from esp-rs template
        mcu = CHIP_TO_TEMPLATE_MCU.get(config.chip, "esp32c3")

        # cargo-generate arguments
        args = [
            "cargo-generate",
            "esp-rs/esp-template",
            "--name",
            config.name,
            "-d",
            f"mcu={mcu}",
            "-d",
            "advanced=true",
            "-d",
            "devcontainer=false",
            "-d",
            "wokwi=false",
            "-d",
            "ci=false",
            "-d",
            "std=false",  # Use no_std for embedded
        ]

        try:
            subprocess.run(
                args,
                cwd=output_path.parent,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Failed to generate project: {e}", file=sys.stderr)
            print(f"stdout: {e.stdout.decode()}", file=sys.stderr)
            print(f"stderr: {e.stderr.decode()}", file=sys.stderr)
            return False

        # Now modify the generated Cargo.toml to add ESPHome components
        project_dir = output_path.parent / config.name
        self._inject_esphome_dependencies(config, project_dir)

        return True

    def _inject_esphome_dependencies(
        self, config: ProjectConfig, project_dir: Path
    ) -> None:
        """Inject ESPHome component dependencies into generated Cargo.toml"""
        cargo_toml_path = project_dir / "Cargo.toml"

        with open(cargo_toml_path, "rb") as f:
            cargo_data = tomli.load(f)

        # Add ESPHome component dependencies
        if "dependencies" not in cargo_data:
            cargo_data["dependencies"] = {}

        # Collect all components
        component_deps = {}
        for component in config.components:
            component_deps[component] = ComponentDependency(
                name=component,
                path=str(self.workspace_path / "components" / component),
                needs_chip_feature=component in CHIP_DEPENDENT_COMPONENTS,
            )

        # Always include core
        if "esphome-core" not in component_deps:
            component_deps["esphome-core"] = ComponentDependency(
                name="esphome-core",
                path=str(self.workspace_path / "core"),
                needs_chip_feature=True,
            )

        # Add component dependencies
        for comp_name, comp_dep in component_deps.items():
            cargo_data["dependencies"][comp_name] = comp_dep.to_toml(config.chip)

        # Ensure features section exists
        if "features" not in cargo_data:
            cargo_data["features"] = {}

        # Add chip feature
        features = []
        for comp_name, comp_dep in component_deps.items():
            if comp_dep.needs_chip_feature:
                features.append(f"{comp_name}/{config.chip}")

        cargo_data["features"][config.chip] = features
        cargo_data["features"]["default"] = [config.chip]

        # Write back
        with open(cargo_toml_path, "wb") as f:
            tomli_w.dump(cargo_data, f)

    def generate_project_cargo_toml(
        self, config: ProjectConfig, output_path: Path
    ) -> None:
        """Generate Cargo.toml for a project with correct dependencies (fallback)"""

        # Collect all components and their dependencies
        component_deps = {}

        for component in config.components:
            component_deps[component] = ComponentDependency(
                name=component,
                path=str(self.workspace_path / "components" / component),
                needs_chip_feature=component in CHIP_DEPENDENT_COMPONENTS,
            )

        # Always include core
        if "esphome-core" not in component_deps:
            component_deps["esphome-core"] = ComponentDependency(
                name="esphome-core",
                path=str(self.workspace_path / "core"),
                needs_chip_feature=True,
            )

        # Generate Cargo.toml
        cargo_toml = {
            "package": {
                "name": config.name,
                "version": "0.1.0",
                "edition": "2024",
            },
            "dependencies": {},
            "features": self._generate_features(config.chip, component_deps),
            "profile": {
                "release": {
                    "opt-level": "s",
                    "lto": True,
                    "codegen-units": 1,
                    "strip": True,
                },
                "dev": {
                    "opt-level": 1,
                },
            },
        }

        # Add component dependencies
        for comp_name, comp_dep in component_deps.items():
            cargo_toml["dependencies"][comp_name] = comp_dep.to_toml(config.chip)

        # Add platform dependencies
        cargo_toml["dependencies"].update(self._get_platform_dependencies(config.chip))

        # Write Cargo.toml
        output_file = output_path / "Cargo.toml"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "wb") as f:
            tomli_w.dump(cargo_toml, f)

    def _generate_features(
        self, chip: str, components: dict[str, ComponentDependency]
    ) -> dict[str, list[str]]:
        """Generate feature flags for the project"""

        # Build feature list
        features = []
        for comp_name, comp_dep in components.items():
            if comp_dep.needs_chip_feature:
                features.append(f"{comp_name}/{chip}")

        # Add platform HAL features
        features.append(f"esp-hal/{chip}")

        # Add WiFi if available for this chip
        if chip not in ["esp32c5", "esp32p4"] and any(
            "wifi" in comp for comp in components
        ):
            features.append(f"esp-wifi/{chip}")

        return {
            chip: features,
            "default": [chip],  # Make chip feature default
        }

    def _get_platform_dependencies(self, chip: str) -> dict:
        """Get required platform dependencies for the chip"""
        return {
            "esp-hal": {"version": "1.0.0", "features": ["unstable", chip]},
            "esp-backtrace": {
                "version": "0.11",
                "features": ["panic-handler", "exception-handler"],
            },
            "esp-println": "0.9",
            "embassy-executor": {"version": "0.9.1", "features": ["executor-thread"]},
            "embassy-time": {"version": "0.5.0", "features": ["generic-queue-8"]},
        }

    def generate_cargo_config(self, chip: str, output_path: Path) -> None:
        """Generate .cargo/config.toml with correct target and runner"""

        # Map chips to targets
        target_map = {
            "esp32": "xtensa-esp32-none-elf",
            "esp32s2": "xtensa-esp32s2-none-elf",
            "esp32s3": "xtensa-esp32s3-none-elf",
            "esp32c3": "riscv32imc-unknown-none-elf",
            "esp32c2": "riscv32imc-unknown-none-elf",
            "esp32c5": "riscv32imac-unknown-none-elf",
            "esp32c6": "riscv32imac-unknown-none-elf",
            "esp32h2": "riscv32imac-unknown-none-elf",
            "esp32p4": "riscv32imafc-unknown-none-elf",
        }

        target = target_map.get(chip)
        if not target:
            raise ValueError(f"No target mapping for chip {chip}")

        config = {
            "build": {
                "target": target,
            },
            "target": {target: {"runner": "espflash flash --monitor"}},
            "unstable": {"build-std": ["core"]},
        }

        config_dir = output_path / ".cargo"
        config_dir.mkdir(parents=True, exist_ok=True)

        with open(config_dir / "config.toml", "wb") as f:
            tomli_w.dump(config, f)

    def validate_workspace_consistency(self) -> list[str]:
        """
        Validate that all workspace components use workspace dependencies correctly.
        Returns list of issues found.
        """
        issues = []

        # Check each component
        for component_dir in (self.workspace_path / "components").iterdir():
            if not component_dir.is_dir():
                continue

            cargo_toml = component_dir / "Cargo.toml"
            if not cargo_toml.exists():
                continue

            with open(cargo_toml, "rb") as f:
                data = tomli.load(f)

            component_name = data.get("package", {}).get("name", component_dir.name)

            # Check dependencies use workspace = true
            for dep_name, dep_spec in data.get("dependencies", {}).items():
                if (
                    dep_name.startswith("esphome-")
                    or dep_name in self.workspace_deps
                    and isinstance(dep_spec, dict)
                    and not dep_spec.get("workspace")
                    and "version" in dep_spec
                ):
                    issues.append(
                        f"{component_name}: Dependency '{dep_name}' should use "
                        "'{ workspace = true }' instead of version"
                    )

            # Check features forward to dependencies correctly
            features = data.get("features", {})
            for chip in SUPPORTED_CHIPS:
                if chip in features:
                    chip_features = features[chip]

                    # Should forward to esphome-core
                    if f"esphome-core/{chip}" not in chip_features:
                        issues.append(
                            f"{component_name}: Feature '{chip}' should forward to "
                            f"'esphome-core/{chip}'"
                        )

        return issues


def example_usage():
    """Example of how to use this module in the code generator"""

    # Initialize dependency manager
    dep_manager = DependencyManager(workspace_path=Path("./embhome"))

    # Validate workspace before generating
    issues = dep_manager.validate_workspace_consistency()
    if issues:
        print("Workspace validation issues:")
        for issue in issues:
            print(f"  - {issue}")

    # Create project configuration
    config = ProjectConfig(
        name="my-esphome-device",
        chip="esp32c3",
        components=[
            "esphome-wifi",
            "esphome-api",
            "esphome-gpio",
            "esphome-sensor",
        ],
    )

    # Try to use esp-generate first (recommended)
    output_path = Path("./generated-project")
    if dep_manager.generate_project_with_esp_generate(config, output_path):
        print(f"Generated project using esp-generate at {output_path}")
    else:
        # Fallback to manual generation
        print("cargo-generate not found, using fallback generation")
        dep_manager.generate_project_cargo_toml(config, output_path)
        dep_manager.generate_cargo_config(config.chip, output_path)
        print(f"Generated project at {output_path}")


if __name__ == "__main__":
    example_usage()
