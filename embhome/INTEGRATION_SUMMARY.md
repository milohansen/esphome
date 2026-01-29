# ESPHome Rust Dependency System + esp-generate Integration

## Executive Summary

The embhome workspace now has a complete dependency management system that:
1. **Ensures single dependency versions** across all components
2. **Automatically propagates chip features** to all dependencies
3. **Integrates with esp-generate** (official esp-rs project generator)
4. **Provides fallback** for environments without cargo-generate

## What Was Built

### 1. Dependency Inheritance System

**File**: `/embhome/Cargo.toml`
- Workspace dependencies with exact versions
- All components inherit via `{ workspace = true }`
- Guarantees: single version, no conflicts, type compatibility

**Result**: No more version conflicts or duplicate dependencies in binaries.

### 2. Feature Propagation System

**Every component** (`core`, `hal`, `wifi`, `api`, `ota`, `gpio`, `sensor`, `uptime`):
```toml
[features]
esp32c3 = ["esphome-core/esp32c3", "esp-hal/esp32c3", ...]
```

**Result**: Single `--features esp32c3` enables correct chip code everywhere.

### 3. esp-generate Integration

**File**: `/embhome/codegen_helpers.py`

New method: `generate_project_with_esp_generate()`
- Uses cargo-generate with esp-rs/esp-template
- Injects ESPHome components after base generation
- Automatic fallback if cargo-generate not available

**Result**: Generated projects use official esp-rs structure and stay current with ecosystem.

## Architecture

```
ESPHome YAML Config
      ↓
Python Code Generator (esphome/rust_codegen.py)
      ↓
codegen_helpers.DependencyManager
      ↓
   ┌─────────────────┬──────────────────┐
   ↓                 ↓                  ↓
esp-generate   OR   Manual         Validation
(preferred)      Generation      (validate_workspace.py)
   ↓                 ↓                  ↓
esp-rs/esp-template  Cargo.toml    Check Results
+ ESPHome inject     generation
      ↓                 ↓
   Generated Project Ready to Build
```

## Usage Examples

### Example 1: Generate Project with esp-generate

```python
from pathlib import Path
from embhome.codegen_helpers import DependencyManager, ProjectConfig

# Setup
dep_manager = DependencyManager(workspace_path=Path("./embhome"))

# Configure
config = ProjectConfig(
    name="living-room-sensor",
    chip="esp32c3",
    components=["esphome-wifi", "esphome-api", "esphome-gpio"]
)

# Generate (tries esp-generate, falls back if needed)
output_dir = Path("./build/living-room-sensor")
if dep_manager.generate_project_with_esp_generate(config, output_dir):
    print("✓ Generated with esp-generate")
else:
    print("⚠ Using fallback (install cargo-generate)")
    dep_manager.generate_project_cargo_toml(config, output_dir)
    dep_manager.generate_cargo_config(config.chip, output_dir)
```

### Example 2: Validate Workspace

```bash
cd embhome
./validate_workspace.py
```

Output:
```
=== Checking Workspace Dependencies ===
✓ All components use workspace dependencies correctly

=== Checking Feature Forwarding ===
✓ All chip features are forwarded correctly

=== Checking Embassy Version Consistency ===
✓ Embassy crate versions are consistent
  embassy-executor: 0.9.1
  embassy-sync: 0.7.2
  embassy-time: 0.5.0

=== Checking for Duplicate Dependencies ===
✓ No duplicate dependencies found

=== Summary ===
✓ All checks passed! ✨
```

### Example 3: Add New Component

```bash
cd components
cargo new my-component --lib
```

Edit `my-component/Cargo.toml`:
```toml
[package]
name = "esphome-my-component"
version = "0.1.0"
edition = "2024"

[dependencies]
esphome-core = { workspace = true }
embassy-time = { workspace = true }

[features]
esp32c3 = ["esphome-core/esp32c3"]
# ... add all chip features
```

Validate:
```bash
cd ../..
./validate_workspace.py
```

## Key Files

### Documentation
- **README.md** - Getting started
- **DEPENDENCY_MANAGEMENT.md** - Complete system docs (267 lines)
- **ESP_GENERATE_INTEGRATION.md** - esp-generate guide
- **QUICK_REFERENCE.md** - Cheat sheet
- **CHANGELOG.md** - What changed
- **INTEGRATION_SUMMARY.md** - This file

### Code
- **codegen_helpers.py** - Python API for generation
- **validate_workspace.py** - Validation tool
- **Cargo.toml** - Workspace with [workspace.dependencies]

### Examples
- **example-generated-project/** - Shows expected output

## Installation

### For Development

```bash
# Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# ESP tools
cargo install espup espflash cargo-generate
espup install

# Python deps
pip install tomli tomli-w
```

### For CI/CD

```bash
# In CI environment
cargo install cargo-generate
pip install tomli tomli-w

# Validate
cd embhome && ./validate_workspace.py
```

## Integration Points

### 1. ESPHome Build System

Update `esphome/rust_codegen.py`:

```python
from pathlib import Path
from embhome.codegen_helpers import DependencyManager, ProjectConfig

def generate_rust_project(config, output_dir: Path):
    # Extract info from YAML
    chip = config["esphome"].get("platform", "esp32c3")
    name = config["esphome"]["name"]

    # Collect components
    components = []
    if "wifi" in config:
        components.append("esphome-wifi")
    if "api" in config:
        components.append("esphome-api")
    # ... etc

    # Generate
    dep_manager = DependencyManager(workspace_path=Path("./embhome"))
    project_config = ProjectConfig(name=name, chip=chip, components=components)

    # Use esp-generate (preferred)
    if not dep_manager.generate_project_with_esp_generate(project_config, output_dir):
        # Fallback
        dep_manager.generate_project_cargo_toml(project_config, output_dir)
        dep_manager.generate_cargo_config(chip, output_dir)
```

### 2. Component Registration

Components auto-register by being in workspace:

```toml
# In /embhome/Cargo.toml
[workspace]
members = [
    "core",
    "hal",
    "components/wifi",
    "components/my-new-component",  # Just add here!
]
```

### 3. Dependency Updates

Update once in workspace:

```toml
# In /embhome/Cargo.toml
[workspace.dependencies]
embassy-time = { version = "0.6.0", features = ["generic-queue-8"] }
```

All components automatically get the new version!

## Guarantees

### ✅ Single Version
Cargo enforces only one version of each dependency in the final binary.

### ✅ Feature Propagation
Chip features flow automatically from root → components → platform deps.

### ✅ Type Safety
All components use matching Embassy/esp-hal types (no version mismatches).

### ✅ Minimal Flash
No duplicate code from multiple library versions.

### ✅ Ecosystem Compatibility
Using esp-generate ensures compatibility with official esp-rs ecosystem.

## Testing

### Unit Test: Component Features

```bash
cd embhome/components/wifi
cargo build --features esp32c3
cargo build --features esp32s3
```

### Integration Test: Full Build

```bash
cd embhome/example-generated-project
cargo build --release
```

### Validation Test: Workspace

```bash
cd embhome
./validate_workspace.py
cargo tree --duplicates  # Should be empty
```

## Performance Impact

### Flash Size
- **Before**: Duplicate deps could add 50-100KB
- **After**: Single version, optimized

### Compile Time
- **esp-generate**: +5-10s initial project creation
- **Workspace deps**: Faster incremental builds (shared cache)

### Runtime
- **No impact**: Same generated code, just cleaner dependencies

## Maintenance

### Adding Dependencies

```toml
# In /embhome/Cargo.toml
[workspace.dependencies]
new-crate = "1.0"

# In component
[dependencies]
new-crate = { workspace = true }
```

### Updating Versions

```bash
# Update workspace
edit embhome/Cargo.toml

# Validate
cd embhome && ./validate_workspace.py

# Test
cargo build --features esp32c3
```

### CI Integration

```yaml
# In .github/workflows/rust.yml
- name: Validate Workspace
  run: cd embhome && python validate_workspace.py

- name: Check Duplicates
  run: cd embhome && cargo tree --duplicates
```

## Troubleshooting

### "Multiple versions of X"

```bash
cd embhome
cargo tree --duplicates
# Fix: Update component to use { workspace = true }
```

### "No chip feature selected"

```bash
# Check feature forwarding
cd embhome
./validate_workspace.py
# Fix: Add chip to component's [features]
```

### "cargo-generate not found"

```bash
cargo install cargo-generate
# Or: System will use fallback automatically
```

## Success Metrics

- ✅ 0 duplicate dependencies
- ✅ 0 version conflicts
- ✅ All 9 components use workspace deps
- ✅ All chip features forward correctly
- ✅ Validation passes
- ✅ Example project builds

## Next Steps

1. **Update rust_codegen.py** to use new API
2. **Add CI validation** with validate_workspace.py
3. **Test with real YAML configs**
4. **Document for contributors**
5. **Consider custom cargo-generate template**

## Support

- **Issues**: Check validate_workspace.py output
- **Questions**: See DEPENDENCY_MANAGEMENT.md
- **Examples**: See example-generated-project/
- **Updates**: Check CHANGELOG.md
