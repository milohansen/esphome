# ESP-Generate Integration Guide

ESPHome Rust code generation now uses **esp-rs/esp-template** via `cargo-generate` as the foundation for project scaffolding. This ensures maximum compatibility with the esp-rs ecosystem and reduces maintenance burden.

## Architecture

### Two-Stage Generation Process

```
┌─────────────────────────────────────────────────┐
│  Stage 1: esp-generate (cargo-generate)         │
│  Creates base ESP Rust project with:            │
│  - Correct esp-hal setup                        │
│  - Embassy configuration                        │
│  - Build toolchain                              │
│  - Target configuration                         │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  Stage 2: ESPHome Component Injection           │
│  Modifies generated Cargo.toml to add:          │
│  - esphome-core, esphome-hal                    │
│  - Component crates (wifi, api, gpio, etc.)     │
│  - Chip feature propagation                     │
└─────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

```bash
# Install cargo-generate (required for esp-generate)
cargo install cargo-generate

# Install espflash (for flashing devices)
cargo install espflash

# Install ESP Rust toolchain
cargo install espup
espup install

# Python dependencies
pip install tomli tomli-w
```

## Usage

### From Python Code Generator

```python
from pathlib import Path
from embhome.codegen_helpers import DependencyManager, ProjectConfig

# Initialize manager
dep_manager = DependencyManager(workspace_path=Path("./embhome"))

# Create configuration from YAML
config = ProjectConfig(
    name="my-device",
    chip="esp32c3",  # From esphome.platform in YAML
    components=[
        "esphome-wifi",
        "esphome-api",
        "esphome-gpio",
    ]
)

# Generate using esp-generate (preferred)
output_dir = Path("./build/my-device")
if dep_manager.generate_project_with_esp_generate(config, output_dir):
    print("✓ Generated with esp-generate")
else:
    # Fallback if cargo-generate not installed
    print("⚠ Using fallback generation (install cargo-generate for best results)")
    dep_manager.generate_project_cargo_toml(config, output_dir)
    dep_manager.generate_cargo_config(config.chip, output_dir)
```

### Manual Usage (Testing)

```bash
# Generate base project
cargo generate esp-rs/esp-template \
    --name test-device \
    -d mcu=esp32c3 \
    -d advanced=true \
    -d std=false

# Then inject ESPHome dependencies
cd test-device
python -c "
from pathlib import Path
from embhome.codegen_helpers import DependencyManager, ProjectConfig

config = ProjectConfig(name='test-device', chip='esp32c3', components=['esphome-wifi'])
manager = DependencyManager(Path('../embhome'))
manager._inject_esphome_dependencies(config, Path('.'))
"
```

## What esp-generate Provides

The esp-rs template generates:

1. **Cargo.toml** with:
   - Correct esp-hal version and features
   - Embassy dependencies with correct features
   - Platform-specific configuration
   - Optimized build profiles

2. **.cargo/config.toml** with:
   - Correct target triple for chip architecture
   - espflash runner configuration
   - Build-std setup

3. **src/main.rs** with:
   - Embassy executor setup
   - Peripheral initialization
   - Timer configuration
   - Basic application structure

4. **build.rs** (if needed):
   - Platform-specific build logic

5. **rust-toolchain.toml**:
   - Correct Rust toolchain version

## What ESPHome Adds

After esp-generate creates the base, ESPHome injects:

1. **Component Dependencies**:
```toml
[dependencies]
esphome-core = { path = "../embhome/core", features = ["esp32c3"] }
esphome-wifi = { path = "../embhome/components/wifi", features = ["esp32c3"] }
esphome-api = { path = "../embhome/components/api", features = ["esp32c3"] }
```

2. **Feature Forwarding**:
```toml
[features]
esp32c3 = [
    "esphome-core/esp32c3",
    "esphome-wifi/esp32c3",
    "esphome-api/esp32c3",
]
default = ["esp32c3"]
```

3. **Modified src/main.rs**:
   - Component initialization code
   - Actor task spawning
   - ESPHome application setup

## Benefits of esp-generate Integration

### ✅ Maintained by esp-rs Team
- Stays up-to-date with esp-hal changes
- Benefits from community improvements
- Follows best practices for ESP Rust

### ✅ Correct Out-of-Box Setup
- No need to manually configure targets
- Proper Embassy feature selection
- Correct linker scripts and memory layout

### ✅ Reduced Maintenance
- ESPHome only manages component injection
- Template changes automatically available
- Less code to maintain in ESPHome

### ✅ Familiar to ESP Rust Users
- Same base as other ESP Rust projects
- Easy for contributors to understand
- Compatible with esp-rs documentation

## Fallback Mode

If `cargo-generate` is not installed, the system falls back to manual generation:

```python
# Fallback automatically used if cargo-generate not found
dep_manager.generate_project_cargo_toml(config, output_path)
dep_manager.generate_cargo_config(config.chip, output_path)
```

**Recommendation**: Install `cargo-generate` for production use. Fallback is provided for development/testing only.

## Template Options

The esp-generate call uses these options:

```bash
cargo-generate esp-rs/esp-template \
    --name <device-name> \
    -d mcu=<chip>          # esp32, esp32c3, esp32s2, esp32s3, etc.
    -d advanced=true        # Enable advanced features
    -d devcontainer=false   # No devcontainer (ESPHome handles environment)
    -d wokwi=false         # No Wokwi simulation
    -d ci=false            # No CI templates
    -d std=false           # no_std (embedded)
```

## Chip Mapping

ESPHome chip names map to esp-template MCU names:

| ESPHome Chip | esp-template MCU | Architecture |
|--------------|------------------|--------------|
| esp32        | esp32            | Xtensa       |
| esp32c3      | esp32c3          | RISC-V       |
| esp32s2      | esp32s2          | Xtensa       |
| esp32s3      | esp32s3          | Xtensa       |
| esp32c2      | esp32c2          | RISC-V       |
| esp32c5      | esp32c5          | RISC-V       |
| esp32c6      | esp32c6          | RISC-V       |
| esp32h2      | esp32h2          | RISC-V       |
| esp32p4      | esp32p4          | RISC-V       |

## Integration with ESPHome Build System

### In esphome/rust_codegen.py

```python
from embhome.codegen_helpers import DependencyManager, ProjectConfig

def generate_rust_project(config, output_dir: Path):
    # Extract chip from config
    chip = config["esphome"].get("platform", "esp32c3")

    # Collect components from YAML
    components = []
    if "wifi" in config:
        components.append("esphome-wifi")
    if "api" in config:
        components.append("esphome-api")
    # ... etc

    # Generate project
    dep_manager = DependencyManager(workspace_path=Path("./embhome"))
    project_config = ProjectConfig(
        name=config["esphome"]["name"],
        chip=chip,
        components=components,
    )

    # Use esp-generate
    if not dep_manager.generate_project_with_esp_generate(project_config, output_dir):
        # Fallback
        dep_manager.generate_project_cargo_toml(project_config, output_dir)
        dep_manager.generate_cargo_config(chip, output_dir)
```

## Validation

After generation, validate the project:

```bash
cd generated-project

# Check dependencies
cargo tree --duplicates  # Should be empty

# Check features
cargo tree --features esp32c3 --edges features

# Build
cargo build --release

# Flash
cargo run --release
```

## Troubleshooting

### cargo-generate not found

```bash
cargo install cargo-generate
```

### Template version conflicts

Update cargo-generate:
```bash
cargo install cargo-generate --force
```

### Dependency conflicts

The injected ESPHome dependencies may conflict with template defaults. The injection code handles this by:
1. Preserving esp-hal version from template
2. Adding ESPHome components without replacing core deps
3. Appending features rather than replacing

## Future Improvements

1. **Template Customization**: Fork esp-template with ESPHome-specific defaults
2. **Pre-configured Templates**: Ship ESPHome-specific cargo-generate templates
3. **Component Registry**: Allow components to register their own dependencies
4. **Incremental Updates**: Only regenerate changed files

## References

- [esp-rs/esp-template](https://github.com/esp-rs/esp-template)
- [cargo-generate](https://cargo-generate.github.io/cargo-generate/)
- [esp-hal Documentation](https://docs.esp-rs.org/esp-hal/)
- [Embassy Book](https://embassy.dev/book/)
