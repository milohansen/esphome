# Dependency Inheritance System - Quick Reference

## For Component Developers

### Adding a Dependency to Your Component

```toml
# In your component's Cargo.toml
[dependencies]
embassy-time = { workspace = true }  # Always use workspace = true
```

### Adding Feature Forwarding

```toml
[features]
esp32c3 = [
    "esphome-core/esp32c3",           # Always forward to core
    "esp-hal/esp32c3",                # If you depend on esp-hal
    "esphome-wifi/esp32c3",           # If you depend on esphome-wifi
]
```

### Testing Your Component

```bash
cargo build --features esp32c3
cargo clippy --features esp32c3
```

## For Python Code Generator

### Generate a Project

```python
from codegen_helpers import DependencyManager, ProjectConfig
from pathlib import Path

# Create manager
dep_manager = DependencyManager(workspace_path=Path("./embhome"))

# Create config from YAML
config = ProjectConfig(
    name=device_name,
    chip=platform,  # "esp32c3" from yaml
    components=components_list  # ["esphome-wifi", "esphome-api", ...]
)

# Generate files
dep_manager.generate_project_cargo_toml(config, output_path)
dep_manager.generate_cargo_config(config.chip, output_path)
```

## For Workspace Maintainers

### Adding a New Dependency

1. Add to workspace deps:
```toml
# In /embhome/Cargo.toml
[workspace.dependencies]
new-crate = { version = "1.0", default-features = false }
```

2. Components use it:
```toml
# In component Cargo.toml
[dependencies]
new-crate = { workspace = true }
```

### Updating Dependency Versions

Change once in workspace:
```toml
[workspace.dependencies]
embassy-time = { version = "0.6.0", features = ["generic-queue-8"] }
```

All components automatically use new version!

### Validating Changes

```bash
./validate_workspace.py
cargo tree --duplicates
cargo tree --features esp32c3 --edges features
```

## Common Commands

```bash
# Check workspace structure
cargo metadata --no-deps

# Find duplicates
cargo tree --duplicates

# Show feature flow
cargo tree --features esp32c3 --edges features

# Build all components for ESP32-C3
for d in components/*; do
    (cd $d && cargo build --features esp32c3)
done

# Validate workspace
./validate_workspace.py
```

## Feature Flow Example

When you build with `--features esp32c3`:

```
Your Project (--features esp32c3)
    ↓
esphome-wifi (features = ["esp32c3"])
    ↓ forwards to
    ├─ esphome-core/esp32c3
    ├─ esp-hal/esp32c3
    └─ esp-wifi/esp32c3
```

Result: All dependencies compile for ESP32-C3!

## Chip Support Matrix

| Chip | WiFi | BLE | Notes |
|------|------|-----|-------|
| esp32 | ✅ | ✅ | Original |
| esp32c3 | ✅ | ✅ | RISC-V |
| esp32s2 | ✅ | ❌ | No BLE |
| esp32s3 | ✅ | ✅ | Dual-core |
| esp32c2 | ✅ | ✅ | Low-cost |
| esp32c5 | ❌ | ❌ | No wireless |
| esp32c6 | ✅ | ✅ | WiFi 6 |
| esp32h2 | ❌ | ✅ | Zigbee |
| esp32p4 | ❌ | ❌ | High-perf |

## File Organization

```
embhome/
├── Cargo.toml                  # Workspace + dependency definitions
├── DEPENDENCY_MANAGEMENT.md    # Full docs
├── README.md                   # Getting started
├── QUICK_REFERENCE.md          # This file
├── SUMMARY.md                  # What was changed
├── validate_workspace.py       # Validation tool
├── codegen_helpers.py          # Python API
│
├── core/                       # Core runtime
│   └── Cargo.toml             # Uses workspace deps
├── hal/                        # HAL wrapper
│   └── Cargo.toml             # Forwards chip features to esp-hal
├── config/                     # Config types
│
├── components/
│   ├── wifi/                   # Forwards to esp-wifi
│   ├── api/                    # Network only
│   ├── ota/                    # Forwards to esp-hal (storage)
│   ├── gpio/                   # Forwards to esphome-hal
│   ├── sensor/                 # Base types
│   └── uptime/                 # Timer only
│
└── example-generated-project/  # What Python generates
    ├── Cargo.toml
    ├── .cargo/config.toml
    └── src/main.rs
```

## Troubleshooting

### "Multiple versions of X"
→ Run `cargo tree --duplicates` to find the component
→ Change it to use `{ workspace = true }`

### "No chip feature selected"
→ Check features section forwards to dependencies
→ Build with `--features esp32c3`

### Embassy type incompatibility
→ Run `./validate_workspace.py`
→ Fix any components using old versions

## Best Practices

✅ DO:
- Use `{ workspace = true }`
- Forward chip features
- Test multiple chips
- Validate before commit

❌ DON'T:
- Specify versions in components
- Forget to forward features
- Skip validation
- Use default-features for platform crates

## Getting Help

1. Read [DEPENDENCY_MANAGEMENT.md](DEPENDENCY_MANAGEMENT.md)
2. Check [example-generated-project/](example-generated-project/)
3. Run `./validate_workspace.py`
4. Review existing components for patterns
