#!/usr/bin/env python3
"""
Validate ESPHome Rust workspace dependency configuration

This script checks that:
1. All components use workspace dependencies
2. No version conflicts exist
3. Chip features are properly forwarded
4. No duplicate dependencies in the tree
"""

from pathlib import Path
import subprocess
import sys

import tomli


class Colors:
    """ANSI color codes for terminal output"""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}=== {text} ==={Colors.END}")


def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def check_workspace_dependencies() -> tuple[bool, list[str]]:
    """Check that all components use workspace dependencies"""
    print_header("Checking Workspace Dependencies")

    workspace_root = Path(__file__).parent
    issues = []

    # Load workspace dependencies
    with open(workspace_root / "Cargo.toml", "rb") as f:
        workspace_data = tomli.load(f)

    workspace_deps = set(
        workspace_data.get("workspace", {}).get("dependencies", {}).keys()
    )

    # Check each component
    for component_dir in (workspace_root / "components").iterdir():
        if not component_dir.is_dir() or component_dir.name.startswith("."):
            continue

        cargo_toml = component_dir / "Cargo.toml"
        if not cargo_toml.exists():
            continue

        with open(cargo_toml, "rb") as f:
            data = tomli.load(f)

        component_name = data.get("package", {}).get("name", component_dir.name)

        # Check dependencies
        for dep_name, dep_spec in data.get("dependencies", {}).items():
            # Skip path-only dependencies (local workspace crates)
            if (
                isinstance(dep_spec, dict)
                and "path" in dep_spec
                and "workspace" not in dep_spec
            ):
                # Check if it should be using workspace = true
                if dep_name in workspace_deps:
                    issues.append(
                        f"{component_name}: '{dep_name}' is in workspace deps but uses path instead of workspace = true"
                    )
                continue

            # Check if it's a workspace dependency
            if dep_name in workspace_deps:
                if not isinstance(dep_spec, dict) or not dep_spec.get("workspace"):
                    issues.append(
                        f"{component_name}: '{dep_name}' should use {{ workspace = true }}"
                    )
            elif (
                isinstance(dep_spec, dict)
                and "version" in dep_spec
                and dep_name not in ["serde"]
            ):  # Some deps have component-specific features
                issues.append(
                    f"{component_name}: '{dep_name}' specifies version directly, should be in workspace deps"
                )

    # Check core and hal too
    for crate_dir in [workspace_root / "core", workspace_root / "hal"]:
        cargo_toml = crate_dir / "Cargo.toml"
        if cargo_toml.exists():
            with open(cargo_toml, "rb") as f:
                data = tomli.load(f)

            crate_name = data.get("package", {}).get("name")

            for dep_name, dep_spec in data.get("dependencies", {}).items():
                if (
                    dep_name in workspace_deps
                    and not isinstance(dep_spec, dict)
                    or not dep_spec.get("workspace")
                ):
                    issues.append(
                        f"{crate_name}: '{dep_name}' should use {{ workspace = true }}"
                    )

    if not issues:
        print_success("All components use workspace dependencies correctly")
        return True, []
    for issue in issues:
        print_error(issue)
    return False, issues


def check_feature_forwarding() -> tuple[bool, list[str]]:
    """Check that chip features are forwarded correctly"""
    print_header("Checking Feature Forwarding")

    workspace_root = Path(__file__).parent
    issues = []

    chips = [
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

    # Components that must forward features
    components_to_check = [
        ("components/wifi", ["esphome-core", "esp-hal", "esp-wifi"]),
        ("components/ota", ["esphome-core", "esp-hal"]),
        ("components/api", ["esphome-core"]),
        ("components/gpio", ["esphome-core", "esphome-hal"]),
        ("hal", ["esphome-core", "esp-hal"]),
    ]

    for component_path, required_forwards in components_to_check:
        cargo_toml = workspace_root / component_path / "Cargo.toml"
        if not cargo_toml.exists():
            continue

        with open(cargo_toml, "rb") as f:
            data = tomli.load(f)

        component_name = data.get("package", {}).get("name")
        features = data.get("features", {})

        # Check each chip feature
        for chip in chips:
            if chip not in features:
                issues.append(f"{component_name}: Missing feature '{chip}'")
                continue

            chip_features = features[chip]

            # Check required forwards
            for required in required_forwards:
                # Skip wifi features for chips without WiFi
                if "wifi" in required and chip in ["esp32c5", "esp32p4"]:
                    continue

                expected = f"{required}/{chip}"
                if expected not in chip_features:
                    issues.append(
                        f"{component_name}: Feature '{chip}' doesn't forward to '{expected}'"
                    )

    if not issues:
        print_success("All chip features are forwarded correctly")
        return True, []
    for issue in issues:
        print_error(issue)
    return False, issues


def check_duplicate_dependencies() -> tuple[bool, list[str]]:
    """Check for duplicate dependencies using cargo tree"""
    print_header("Checking for Duplicate Dependencies")

    try:
        result = subprocess.run(
            ["cargo", "tree", "--duplicates"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
            check=False,
        )

        if result.returncode == 0 and not result.stdout.strip():
            print_success("No duplicate dependencies found")
            return True, []
        issues = result.stdout.strip().split("\n") if result.stdout.strip() else []
        if issues:
            print_error("Found duplicate dependencies:")
            for issue in issues:
                print(f"  {issue}")
        return False, issues

    except FileNotFoundError:
        print_warning("cargo not found, skipping duplicate check")
        return True, []
    except Exception as e:
        print_warning(f"Could not run cargo tree: {e}")
        return True, []


def check_embassy_versions() -> tuple[bool, list[str]]:
    """Check that all Embassy crates use the same version"""
    print_header("Checking Embassy Version Consistency")

    workspace_root = Path(__file__).parent
    issues = []

    with open(workspace_root / "Cargo.toml", "rb") as f:
        workspace_data = tomli.load(f)

    workspace_deps = workspace_data.get("workspace", {}).get("dependencies", {})

    # Embassy crates that must be version-aligned
    embassy_crates = [
        "embassy-executor",
        "embassy-time",
        "embassy-sync",
        "embassy-net",
        "embassy-futures",
    ]

    versions = {}
    for crate in embassy_crates:
        if crate in workspace_deps:
            dep_spec = workspace_deps[crate]
            if isinstance(dep_spec, dict):
                version = dep_spec.get("version")
            else:
                version = dep_spec
            versions[crate] = version

    # Check versions are reasonable
    executor_version = (
        versions.get("embassy-executor", "").split(".")[1]
        if "embassy-executor" in versions
        else None
    )
    time_version = (
        versions.get("embassy-time", "").split(".")[1]
        if "embassy-time" in versions
        else None
    )
    sync_version = (
        versions.get("embassy-sync", "").split(".")[1]
        if "embassy-sync" in versions
        else None
    )

    # These should be relatively close (within a few minor versions)
    if executor_version and time_version and sync_version:
        if abs(int(executor_version) - int(time_version)) > 3:
            issues.append(
                f"embassy-executor ({versions['embassy-executor']}) and "
                f"embassy-time ({versions['embassy-time']}) versions are too far apart"
            )
        if abs(int(executor_version) - int(sync_version)) > 3:
            issues.append(
                f"embassy-executor ({versions['embassy-executor']}) and "
                f"embassy-sync ({versions['embassy-sync']}) versions are too far apart"
            )

    if not issues:
        print_success("Embassy crate versions are consistent")
        for crate, version in sorted(versions.items()):
            print(f"  {crate}: {version}")
        return True, []
    for issue in issues:
        print_error(issue)
    return False, issues


def main():
    """Run all validation checks"""
    print(f"{Colors.BOLD}ESPHome Rust Workspace Validation{Colors.END}")
    print(f"Workspace: {Path(__file__).parent}")

    all_passed = True
    all_issues = []

    # Run checks
    checks = [
        check_workspace_dependencies,
        check_feature_forwarding,
        check_embassy_versions,
        check_duplicate_dependencies,
    ]

    for check in checks:
        passed, issues = check()
        all_passed = all_passed and passed
        all_issues.extend(issues)

    # Summary
    print_header("Summary")
    if all_passed:
        print_success("All checks passed! ✨")
        return 0
    print_error(f"Found {len(all_issues)} issue(s)")
    print("\nRun with --help for guidance on fixing issues")
    return 1


if __name__ == "__main__":
    sys.exit(main())
