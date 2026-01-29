# ESPHome Rust Implementation (embhome)

Modern async Rust implementation of ESPHome using Embassy and esp-hal.

## Quick Start

### Prerequisites

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install ESP toolchain
cargo install espup espflash cargo-generate
espup install

# Install dependencies for code generator
pip install tomli tomli-w
```

**Note**: `cargo-generate` is recommended for project generation. It enables using the official esp-rs templates for better compatibility.

### Validate Workspace

```bash
# Check workspace configuration
./validate_workspace.py

# Check for duplicate dependencies
cargo tree --duplicates
```

### Build a Component

```bash
# Build WiFi component for ESP32-C3
cd components/wifi
cargo build --features esp32c3

# Build OTA component for ESP32
cd ../ota
cargo build --features esp32
```

## Architecture

```
embhome/
├── core/              # Core runtime, component traits, message passing
├── hal/               # Hardware abstraction wrapping esp-hal
├── config/            # Configuration types (serde)
├── components/        # Individual component crates
│   ├── wifi/          # WiFi manager
│   ├── api/           # Native API protocol
│   ├── ota/           # OTA update system
│   ├── gpio/          # GPIO components
│   ├── sensor/        # Sensor base types
│   └── uptime/        # Uptime sensor
├── Cargo.toml         # Workspace with dependency management
└── DEPENDENCY_MANAGEMENT.md  # Full dependency system docs
```

## Dependency Management System

The workspace uses a **centralized dependency inheritance system** to ensure:

### ✅ Single Version Guarantee

Only one version of each dependency across all crates. This prevents:
- Multiple copies of libraries (wastes flash)
- Type incompatibility between components
- Undefined behavior from duplicate globals

### ✅ Automatic Feature Propagation

Chip features (esp32, esp32c3, etc.) automatically propagate to all dependencies:

```toml
# In generated project
[dependencies]
esphome-wifi = { path = "../embhome/components/wifi", features = ["esp32c3"] }

# Automatically enables:
# - esp-hal/esp32c3
# - esp-wifi/esp32c3
# - esphome-core/esp32c3
```

### ✅ Workspace Dependencies

All components use `{ workspace = true }` to inherit versions:

```toml
[dependencies]
embassy-time = { workspace = true }  # Version from workspace
esp-hal = { workspace = true }       # Version from workspace
```

## Adding a New Component

### 1. Create Component Crate

```bash
cd components
cargo new my-component --lib
```

### 2. Configure Cargo.toml

```toml
[package]
name = "esphome-my-component"
version = "0.1.0"
edition = "2024"

[dependencies]
esphome-core = { workspace = true }
embassy-time = { workspace = true }
log = { workspace = true }

[features]
# Forward chip features
esp32 = ["esphome-core/esp32"]
esp32c3 = ["esphome-core/esp32c3"]
esp32s2 = ["esphome-core/esp32s2"]
esp32s3 = ["esphome-core/esp32s3"]
esp32c2 = ["esphome-core/esp32c2"]
esp32c5 = ["esphome-core/esp32c5"]
esp32c6 = ["esphome-core/esp32c6"]
esp32h2 = ["esphome-core/esp32h2"]
esp32p4 = ["esphome-core/esp32p4"]

default = []
```

### 3. Add to Workspace

Edit `/embhome/Cargo.toml`:

```toml
[workspace]
members = [
    # ...
    "components/my-component",
]
```

### 4. Implement Component

See [spec document](../.ai/esphome_rust_full_conversion_spec.md) for component patterns.

## Adding a New Dependency

### 1. Add to Workspace Dependencies

Edit `/embhome/Cargo.toml`:

```toml
[workspace.dependencies]
my-new-crate = { version = "1.0", default-features = false }
```

### 2. Use in Components

```toml
[dependencies]
my-new-crate = { workspace = true }
```

**Never specify version in component crates!**

### 3. If Dependency Has Chip Features

```toml
# In workspace
[workspace.dependencies]
my-chip-crate = { version = "1.0", default-features = false }

# In component that uses it
[features]
esp32c3 = [
    "esphome-core/esp32c3",
    "my-chip-crate/esp32c3"  # Forward chip feature
]
```

## Code Generation for Projects

The Python code generator uses `codegen_helpers.py` with **esp-generate integration**:

```python
from codegen_helpers import DependencyManager, ProjectConfig

# Initialize
dep_manager = DependencyManager(workspace_path=Path("./embhome"))

# Validate workspace first
issues = dep_manager.validate_workspace_consistency()
if issues:
    raise ValueError(f"Workspace has issues: {issues}")

# Create project
config = ProjectConfig(
    name="my-device",
    chip="esp32c3",
    components=["esphome-wifi", "esphome-api", "esphome-gpio"]
)

# Generate using esp-generate (recommended)
if dep_manager.generate_project_with_esp_generate(config, output_path):
    print("✓ Generated with esp-generate")
else:
    # Fallback if cargo-generate not installed
    dep_manager.generate_project_cargo_toml(config, output_path)
    dep_manager.generate_cargo_config(config.chip, output_path)
```

See [ESP_GENERATE_INTEGRATION.md](ESP_GENERATE_INTEGRATION.md) for details.

## Supported Chips

| Chip     | Architecture | WiFi | Notes |
|----------|-------------|------|-------|
| ESP32    | Xtensa      | ✅   | Original ESP32 |
| ESP32-C3 | RISC-V      | ✅   | Low-cost, single-core |
| ESP32-S2 | Xtensa      | ✅   | No Bluetooth |
| ESP32-S3 | Xtensa      | ✅   | Dual-core, AI acceleration |
| ESP32-C2 | RISC-V      | ✅   | Ultra-low-cost |
| ESP32-C5 | RISC-V      | ❌   | No WiFi |
| ESP32-C6 | RISC-V      | ✅   | WiFi 6, Zigbee |
| ESP32-H2 | RISC-V      | ❌   | Bluetooth 5, Zigbee |
| ESP32-P4 | RISC-V      | ❌   | High-performance, no wireless |

## Validation

### Run Full Validation

```bash
./validate_workspace.py
```

Checks:
- ✅ All components use workspace dependencies
- ✅ Chip features forward correctly
- ✅ No duplicate dependencies
- ✅ Embassy versions are consistent

### Check Dependency Tree

```bash
# Show all dependencies
cargo tree

# Show duplicates only
cargo tree --duplicates

# Show feature propagation
cargo tree --features esp32c3 --edges features
```

### Build All Components

```bash
# Test build for ESP32-C3
for component in components/*; do
    echo "Building $component..."
    (cd $component && cargo build --features esp32c3)
done
```

## Common Issues

### Issue: "Multiple versions of X found"

**Cause**: Component not using workspace dependencies

**Fix**: Change to `{ workspace = true }`

```toml
# Before
embassy-time = "0.3.2"

# After
embassy-time = { workspace = true }
```

### Issue: "No chip feature selected"

**Cause**: Feature not forwarded to esp-hal or esp-wifi

**Fix**: Add to component's features

```toml
[features]
esp32c3 = ["esphome-core/esp32c3", "esp-hal/esp32c3"]
```

### Issue: Embassy type incompatibility

**Cause**: Multiple Embassy versions

**Fix**: Run validation and fix any components not using workspace deps

```bash
./validate_workspace.py
cargo tree --duplicates
```

## Development Workflow

### 1. Check Workspace Health

```bash
./validate_workspace.py
```

### 2. Make Changes

Edit component code or dependencies

### 3. Validate Again

```bash
./validate_workspace.py
cargo tree --duplicates
```

### 4. Test Build

```bash
cd components/my-component
cargo build --features esp32c3
cargo clippy --features esp32c3
```

### 5. Update Documentation

Update `DEPENDENCY_MANAGEMENT.md` if you change the dependency structure.

## Component Development Guidelines

### DO:

- ✅ Use `{ workspace = true }` for all dependencies
- ✅ Forward chip features to dependencies that need them
- ✅ Run validation before committing
- ✅ Use `default = []` for component features
- ✅ Test build for multiple chips

### DON'T:

- ❌ Specify version in component crates
- ❌ Use `default-features = true` for platform crates
- ❌ Forget to forward chip features
- ❌ Add new dependencies without updating workspace
- ❌ Mix Embassy versions

## Documentation

- **[DEPENDENCY_MANAGEMENT.md](DEPENDENCY_MANAGEMENT.md)** - Complete dependency system documentation
- **[ESP_GENERATE_INTEGRATION.md](ESP_GENERATE_INTEGRATION.md)** - esp-generate integration guide
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Developer cheat sheet
- **[../..ai/esphome_rust_full_conversion_spec.md](../.ai/esphome_rust_full_conversion_spec.md)** - Full architecture specification
- **[codegen_helpers.py](codegen_helpers.py)** - Python API for code generation

## References

- [Cargo Workspaces](https://doc.rust-lang.org/cargo/reference/workspaces.html)
- [Cargo Features](https://doc.rust-lang.org/cargo/reference/features.html)
- [esp-hal](https://github.com/esp-rs/esp-hal)
- [esp-wifi](https://github.com/esp-rs/esp-wifi)
- [Embassy](https://embassy.dev/)

## License

MIT OR Apache-2.0 (same as ESPHome)
