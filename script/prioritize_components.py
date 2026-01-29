#!/usr/bin/env python3
"""Prioritize components based on dependencies and importance."""

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class ComponentInfo:
    name: str
    dependencies: list[str] = field(default_factory=list)
    auto_load: list[str] = field(default_factory=list)
    codeowners: list[str] = field(default_factory=list)
    is_core_owned: bool = False
    structures: set[str] = field(default_factory=set)
    dependent_count: int = 0
    priority_score: float = 0.0


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

        # Extract CODEOWNERS
        codeowners_match = re.search(r"CODEOWNERS\s*=\s*\[(.*?)\]", content, re.DOTALL)
        if codeowners_match:
            owners_str = codeowners_match.group(1)
            info.codeowners = [
                o.strip().strip("\"'") for o in owners_str.split(",") if o.strip()
            ]
            info.is_core_owned = "@esphome/core" in info.codeowners

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
        ]

        component_dir = init_path.parent
        for platform in platform_types:
            if (component_dir / f"{platform}.py").exists():
                info.structures.add(platform)

    except Exception:
        pass

    return info


def analyze_all_components():
    """Analyze all components and calculate priorities."""
    esphome_components = Path("esphome/components")

    components = {}
    dependency_graph = defaultdict(list)

    # First pass: collect all components
    for component_dir in sorted(esphome_components.iterdir()):
        if not component_dir.is_dir() or component_dir.name.startswith("__"):
            continue

        init_file = component_dir / "__init__.py"
        if init_file.exists():
            info = extract_metadata_from_init(init_file)
            components[info.name] = info

            # Build dependency graph
            for dep in info.dependencies:
                dependency_graph[dep].append(info.name)

    # Second pass: count dependents
    for comp_name, info in components.items():
        info.dependent_count = len(dependency_graph[comp_name])

    # Calculate priority scores
    # Priority factors:
    # 1. Core-owned: +100
    # 2. Platform components: +90
    # 3. Base components (sensor, switch, etc.): +80
    # 4. Infrastructure (uart, i2c, spi, network): +70
    # 5. Number of dependents: +1 per dependent

    platform_components = {
        "esp32",
        "esp8266",
        "rp2040",
        "libretiny",
        "bk72xx",
        "rtl87xx",
    }
    base_components = {
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
        "time",
        "valve",
        "media_player",
        "alarm_control_panel",
        "water_heater",
        "event",
        "datetime",
        "update",
    }
    infra_components = {
        "uart",
        "i2c",
        "spi",
        "network",
        "wifi",
        "ethernet",
        "api",
        "logger",
        "ota",
        "mdns",
        "web_server",
        "web_server_base",
        "socket",
        "async_tcp",
    }

    for comp_name, info in components.items():
        score = 0.0

        if info.is_core_owned:
            score += 100

        if comp_name in platform_components:
            score += 90

        if comp_name in base_components:
            score += 80

        if comp_name in infra_components:
            score += 70

        # Add dependent count
        score += info.dependent_count

        info.priority_score = score

    return components, dependency_graph


def generate_priority_report():
    """Generate prioritized component report."""
    components, dep_graph = analyze_all_components()

    # Sort by priority score
    sorted_components = sorted(
        components.values(), key=lambda x: (-x.priority_score, x.name)
    )

    report_path = Path("component_priority.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# ESPHome Component Implementation Priority\n\n")
        f.write(f"Total components: {len(components)}\n\n")

        # Tier 1: Critical (score >= 150)
        tier1 = [c for c in sorted_components if c.priority_score >= 150]
        f.write(f"## Tier 1: Critical Foundation ({len(tier1)})\n\n")
        f.write("These are core-owned, highly depended-upon components.\n\n")
        f.write("| Priority | Component | Score | Dependents | Dependencies | Type |\n")
        f.write("|----------|-----------|-------|------------|--------------|------|\n")
        for i, comp in enumerate(tier1, 1):
            deps_str = ", ".join(comp.dependencies[:2]) if comp.dependencies else "-"
            if len(comp.dependencies) > 2:
                deps_str += f" +{len(comp.dependencies) - 2}"
            type_str = (
                ", ".join(list(comp.structures)[:2]) if comp.structures else "component"
            )
            if len(comp.structures) > 2:
                type_str += f" +{len(comp.structures) - 2}"
            f.write(
                f"| {i} | **{comp.name}** | {comp.priority_score:.0f} | {comp.dependent_count} | {deps_str} | {type_str} |\n"
            )

        # Tier 2: High Priority (100 <= score < 150)
        tier2 = [c for c in sorted_components if 100 <= c.priority_score < 150]
        f.write(f"\n## Tier 2: High Priority ({len(tier2)})\n\n")
        f.write("Core-owned components with moderate dependencies.\n\n")
        f.write("| Priority | Component | Score | Dependents | Dependencies | Type |\n")
        f.write("|----------|-----------|-------|------------|--------------|------|\n")
        for i, comp in enumerate(tier2, 1):
            deps_str = ", ".join(comp.dependencies[:2]) if comp.dependencies else "-"
            if len(comp.dependencies) > 2:
                deps_str += f" +{len(comp.dependencies) - 2}"
            type_str = (
                ", ".join(list(comp.structures)[:2]) if comp.structures else "component"
            )
            if len(comp.structures) > 2:
                type_str += f" +{len(comp.structures) - 2}"
            f.write(
                f"| {i} | **{comp.name}** | {comp.priority_score:.0f} | {comp.dependent_count} | {deps_str} | {type_str} |\n"
            )

        # Tier 3: Medium Priority (50 <= score < 100)
        tier3 = [c for c in sorted_components if 50 <= c.priority_score < 100]
        f.write(f"\n## Tier 3: Medium Priority ({len(tier3)})\n\n")
        f.write("Infrastructure and widely-used components.\n\n")
        f.write("| Component | Score | Dependents | Core |\n")
        f.write("|-----------|-------|------------|------|\n")
        for comp in tier3[:30]:  # Show top 30
            core_mark = "✓" if comp.is_core_owned else ""
            f.write(
                f"| {comp.name} | {comp.priority_score:.0f} | {comp.dependent_count} | {core_mark} |\n"
            )
        if len(tier3) > 30:
            f.write(f"| ... and {len(tier3) - 30} more | | | |\n")

        # Tier 4: Standard (10 <= score < 50)
        tier4 = [c for c in sorted_components if 10 <= c.priority_score < 50]
        f.write(f"\n## Tier 4: Standard Priority ({len(tier4)})\n\n")
        f.write("Components with some dependents.\n\n")
        f.write(f"Top 20: {', '.join(c.name for c in tier4[:20])}\n\n")

        # Tier 5: Low priority (score < 10)
        tier5 = [c for c in sorted_components if c.priority_score < 10]
        f.write(f"\n## Tier 5: Low Priority ({len(tier5)})\n\n")
        f.write("Standalone components with few/no dependents.\n\n")

        # Most depended-upon components
        f.write("\n## Top 20 Most Depended-Upon Components\n\n")
        f.write("| Rank | Component | Dependent Count | Core |\n")
        f.write("|------|-----------|-----------------|------|\n")
        by_dependents = sorted(
            components.values(), key=lambda x: (-x.dependent_count, x.name)
        )
        for i, comp in enumerate(by_dependents[:20], 1):
            core_mark = "✓" if comp.is_core_owned else ""
            f.write(f"| {i} | {comp.name} | {comp.dependent_count} | {core_mark} |\n")

        # Implementation order recommendation
        f.write("\n## Recommended Implementation Order\n\n")
        f.write("### Phase 1: Core Foundation\n")
        f.write("Implement these first (in order):\n\n")
        phase1 = [
            c
            for c in tier1
            if c.dependent_count > 5
            or c.name
            in {
                "esp32",
                "esp8266",
                "sensor",
                "binary_sensor",
                "switch",
                "logger",
                "api",
            }
        ]
        for i, comp in enumerate(phase1[:15], 1):
            f.write(
                f"{i}. **{comp.name}** - {', '.join(list(comp.structures)) if comp.structures else 'base component'}\n"
            )

        f.write("\n### Phase 2: Infrastructure\n")
        f.write("Build communication and device interfaces:\n\n")
        phase2 = [
            c
            for c in tier1 + tier2
            if c not in phase1
            and (
                c.name
                in {
                    "uart",
                    "i2c",
                    "spi",
                    "network",
                    "wifi",
                    "mdns",
                    "ota",
                    "web_server_base",
                }
                or c.dependent_count > 3
            )
        ]
        for i, comp in enumerate(phase2[:15], 1):
            f.write(
                f"{i}. **{comp.name}** - {', '.join(list(comp.structures)) if comp.structures else 'base component'}\n"
            )

        f.write("\n### Phase 3: Common Components\n")
        f.write("Implement frequently-used sensors and devices:\n\n")
        phase3 = [c for c in tier2 + tier3 if c not in phase1 and c not in phase2]
        for i, comp in enumerate(phase3[:20], 1):
            f.write(f"{i}. {comp.name}\n")

        f.write("\n### Phase 4+: Remaining Components\n")
        f.write(
            f"Implement remaining {len(tier4) + len(tier5)} components as needed.\n"
        )

    print(f"\nGenerated priority report: {report_path}")

    # Print summary
    print("\nPriority Tiers:")
    print(
        f"  Tier 1 (Critical):    {len([c for c in sorted_components if c.priority_score >= 150])}"
    )
    print(
        f"  Tier 2 (High):        {len([c for c in sorted_components if 100 <= c.priority_score < 150])}"
    )
    print(
        f"  Tier 3 (Medium):      {len([c for c in sorted_components if 50 <= c.priority_score < 100])}"
    )
    print(
        f"  Tier 4 (Standard):    {len([c for c in sorted_components if 10 <= c.priority_score < 50])}"
    )
    print(
        f"  Tier 5 (Low):         {len([c for c in sorted_components if c.priority_score < 10])}"
    )


if __name__ == "__main__":
    generate_priority_report()
