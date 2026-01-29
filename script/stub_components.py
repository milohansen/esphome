#!/usr/bin/env python3
"""Generate component stubs for embhome with dependency tracking."""

from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class ComponentInfo:
    name: str
    dependencies: list[str] = field(default_factory=list)
    auto_load: list[str] = field(default_factory=list)
    conflicts_with: list[str] = field(default_factory=list)
    codeowners: list[str] = field(default_factory=list)
    multi_conf: bool = False
    structures: set[str] = field(default_factory=set)
    has_platforms: bool = False
    platform_names: list[str] = field(default_factory=list)
    is_core_owned: bool = False


def extract_metadata_from_init(init_path: Path) -> ComponentInfo:
    """Extract metadata from component __init__.py file."""
    info = ComponentInfo(name=init_path.parent.name)

    try:
        with open(init_path, encoding="utf-8") as f:
            content = f.read()

        # Extract DEPENDENCIES
        deps_match = re.search(r"DEPENDENCIES\s*=\s*\[(.*?)\]", content, re.DOTALL)
        if deps_match:
            deps_str = deps_match.group(1)
            info.dependencies = [
                d.strip().strip("\"'") for d in deps_str.split(",") if d.strip()
            ]

        # Extract AUTO_LOAD
        auto_load_match = re.search(r"AUTO_LOAD\s*=\s*\[(.*?)\]", content, re.DOTALL)
        if auto_load_match:
            auto_str = auto_load_match.group(1)
            info.auto_load = [
                a.strip().strip("\"'") for a in auto_str.split(",") if a.strip()
            ]

        # Extract CONFLICTS_WITH
        conflicts_match = re.search(
            r"CONFLICTS_WITH\s*=\s*\[(.*?)\]", content, re.DOTALL
        )
        if conflicts_match:
            conflicts_str = conflicts_match.group(1)
            info.conflicts_with = [
                c.strip().strip("\"'") for c in conflicts_str.split(",") if c.strip()
            ]

        # Extract CODEOWNERS
        codeowners_match = re.search(r"CODEOWNERS\s*=\s*\[(.*?)\]", content, re.DOTALL)
        if codeowners_match:
            owners_str = codeowners_match.group(1)
            info.codeowners = [
                o.strip().strip("\"'") for o in owners_str.split(",") if o.strip()
            ]
            info.is_core_owned = "@esphome/core" in info.codeowners

        # Extract MULTI_CONF
        if "MULTI_CONF" in content:
            multi_match = re.search(r"MULTI_CONF\s*=\s*(True|False)", content)
            if multi_match:
                info.multi_conf = multi_match.group(1) == "True"

    except Exception as e:
        print(f"Warning: Could not parse {init_path}: {e}")

    return info


def analyze_component_structure(component_dir: Path) -> ComponentInfo:
    """Analyze component structure and extract metadata."""
    info = ComponentInfo(name=component_dir.name)

    # Check for __init__.py and extract metadata
    init_file = component_dir / "__init__.py"
    if init_file.exists():
        info = extract_metadata_from_init(init_file)

    # Check for platform files
    platform_types = [
        "sensor",
        "binary_sensor",
        "switch",
        "light",
        "climate",
        "cover",
        "fan",
        "lock",
        "button",
        "number",
        "select",
        "text_sensor",
        "output",
        "display",
        "media_player",
    ]

    for platform in platform_types:
        if (component_dir / f"{platform}.py").exists():
            info.structures.add(platform)

    # Check for platform subdirectories
    for item in component_dir.iterdir():
        if item.is_dir() and not item.name.startswith("__"):
            info.has_platforms = True
            info.platform_names.append(item.name)

    return info


def create_stub_init(component_info: ComponentInfo, stub_dir: Path):
    """Create stub __init__.py file."""
    stub_content = f'''"""
Component: {component_info.name}
Status: NOT IMPLEMENTED

Structure:
- Platform types: {", ".join(component_info.structures) if component_info.structures else "component"}
- Has platform dirs: {component_info.has_platforms}
- Platform subdirs: {", ".join(component_info.platform_names) if component_info.platform_names else "none"}

Dependencies: {", ".join(component_info.dependencies) if component_info.dependencies else "none"}
Auto-load: {", ".join(component_info.auto_load) if component_info.auto_load else "none"}
Codeowners: {", ".join(component_info.codeowners) if component_info.codeowners else "none"}
Core-owned: {"YES" if component_info.is_core_owned else "NO"}
"""

import esphome.codegen as cg
import esphome.config_validation as cv

def validate_component_not_implemented(config):
    raise cv.Invalid(
        f"Component '{component_info.name}' is not yet implemented in embhome. "
        f"This is a stub placeholder."
    )

# Stub schema that raises error
CONFIG_SCHEMA = cv.All(
    cv.Schema({{}}, extra=cv.ALLOW_EXTRA),
    validate_component_not_implemented
)

async def to_code(config):
    """This should never be called due to validation error."""
    pass
'''

    stub_dir.mkdir(parents=True, exist_ok=True)
    with open(stub_dir / "__init__.py", "w", encoding="utf-8") as f:
        f.write(stub_content)


def process_all_components():
    """Process all components and create stubs."""
    esphome_components = Path("esphome/components")
    embhome_components = Path("embhome/components")

    if not esphome_components.exists():
        print(f"Error: {esphome_components} not found")
        return

    # Create embhome/components if it doesn't exist
    embhome_components.mkdir(parents=True, exist_ok=True)

    components = []

    # Process each component
    for component_dir in sorted(esphome_components.iterdir()):
        if not component_dir.is_dir():
            continue

        if component_dir.name.startswith("__"):
            continue

        print(f"Processing: {component_dir.name}")

        # Analyze component
        info = analyze_component_structure(component_dir)
        components.append(info)

        # Create stub
        stub_dir = embhome_components / component_dir.name
        create_stub_init(info, stub_dir)

    # Generate report
    report_path = Path("component_analysis.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# ESPHome Component Analysis\n\n")
        f.write(f"Total components: {len(components)}\n\n")

        # Core-owned components
        core_components = [c for c in components if c.is_core_owned]
        f.write(f"## Core-owned Components ({len(core_components)})\n\n")
        f.write("| Component | Dependencies | Structures | Platforms |\n")
        f.write("|-----------|--------------|------------|----------|\n")
        for comp in sorted(core_components, key=lambda x: x.name):
            deps = ", ".join(comp.dependencies[:3]) + (
                "..." if len(comp.dependencies) > 3 else ""
            )
            structs = ", ".join(comp.structures) if comp.structures else "component"
            platforms = ", ".join(comp.platform_names[:2]) + (
                "..." if len(comp.platform_names) > 2 else ""
            )
            f.write(
                f"| {comp.name} | {deps or '-'} | {structs} | {platforms or '-'} |\n"
            )

        f.write("\n## All Components\n\n")
        f.write("| Component | Core | Dependencies | Structures | Codeowners |\n")
        f.write("|-----------|------|--------------|------------|------------|\n")
        for comp in sorted(components, key=lambda x: x.name):
            core_mark = "✓" if comp.is_core_owned else ""
            deps = ", ".join(comp.dependencies[:2]) + (
                "..." if len(comp.dependencies) > 2 else ""
            )
            structs = ", ".join(list(comp.structures)[:2]) + (
                "..." if len(comp.structures) > 2 else ""
            )
            owners = ", ".join(comp.codeowners[:1]) if comp.codeowners else "-"
            f.write(
                f"| {comp.name} | {core_mark} | {deps or '-'} | {structs or 'component'} | {owners} |\n"
            )

    print(f"\nGenerated report: {report_path}")
    print(f"Created {len(components)} component stubs in {embhome_components}")
    print(f"Core-owned components: {len(core_components)}")


if __name__ == "__main__":
    process_all_components()
