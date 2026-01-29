# ESPHome Rust Dependency Management System

## Overview

The embhome workspace uses a centralized dependency inheritance system to ensure:

1. **Single Version Guarantee**: Only one version of each dependency exists across all crates
2. **Feature Propagation**: Chip-specific features (esp32, esp32c3, etc.) are correctly propagated to all dependencies that need them
3. **Minimal Flash Usage**: No duplicate libraries in the final binary
4. **Type Compatibility**: All crates use the same versions of Embassy, esp-hal, etc.

## Architecture

### Three-Layer Feature Propagation System

```
Generated Project (main.rs)
  └─ Cargo.toml with features = ["esp32c3"]
       ↓
  Component Crates (esphome-wifi, esphome-ota, etc.)
    └─ Forward features to dependencies
         ↓
    Platform Crates (esp-hal, esp-wifi)
      └─ Use chip features to compile correct code
```

### How It Works

1. **Workspace Dependencies** (`/embhome/Cargo.toml`):
   - Defines all external dependencies with exact versions
   - Components inherit from workspace using `{ workspace = true }`
   - Ensures Cargo uses only one version of each dependency

2. **Feature Forwarding** (all component `Cargo.toml` files):
   - Each component defines chip features (esp32, esp32c3, etc.)
   - Features cascade: `esphome-wifi/esp32c3` enables `esp-hal/esp32c3` and `esp-wifi/esp32c3`
   - Root feature enables all necessary features in the dependency tree

3. **Build-Time Selection**:
   - Python code generator creates project with correct chip feature
   - Feature is passed to all dependencies via Cargo's feature resolution
   - Ensures all crates compile for the same chip

## Component Cargo.toml Structure

Every component crate follows this pattern:

```toml
[package]
name = "esphome-component-name"
version = "0.1.0"
edition = "2024"

[dependencies]
# Use workspace = true for all dependencies
esphome-core = { workspace = true }
esp-hal = { workspace = true }
embassy-time = { workspace = true }
# ... other deps

[features]
# Forward chip features to all dependencies that need them
esp32 = ["esphome-core/esp32", "esp-hal/esp32"]
esp32c3 = ["esphome-core/esp32c3", "esp-hal/esp32c3"]
esp32s2 = ["esphome-core/esp32s2", "esp-hal/esp32s2"]
esp32s3 = ["esphome-core/esp32s3", "esp-hal/esp32s3"]
esp32c2 = ["esphome-core/esp32c2", "esp-hal/esp32c2"]
esp32c5 = ["esphome-core/esp32c5", "esp-hal/esp32c5"]
esp32c6 = ["esphome-core/esp32c6", "esp-hal/esp32c6"]
esp32h2 = ["esphome-core/esp32h2", "esp-hal/esp32h2"]
esp32p4 = ["esphome-core/esp32p4", "esp-hal/esp32p4"]

default = []
```

### Rules for Feature Forwarding

1. **Always forward to esphome-core**: Ensures feature is recorded in dependency tree
2. **Forward to direct HAL dependencies**: If you depend on `esp-hal`, forward the chip feature to it
3. **Forward to component dependencies**: If you depend on `esphome-wifi`, forward the chip feature to it
4. **Never use default features**: Use `default = []` to force explicit chip selection

## Adding a New Dependency

### 1. Add to Workspace Dependencies

Edit `/embhome/Cargo.toml`:

```toml
[workspace.dependencies]
# Add your new dependency here
my-new-crate = { version = "1.0", default-features = false }
```

### 2. Use in Component

Edit your component's `Cargo.toml`:

```toml
[dependencies]
my-new-crate = { workspace = true }
```

**Never specify version in component crates!** Always use `{ workspace = true }`.

### 3. If Dependency Has Chip Features

If the dependency has chip-specific features (like esp-hal, esp-wifi):

```toml
[workspace.dependencies]
my-chip-specific-crate = { version = "1.0", default-features = false }

# In your component:
[features]
esp32c3 = [
    "esphome-core/esp32c3",
    "my-chip-specific-crate/esp32c3"  # Forward feature
]
```

## Common Dependency Categories

### Embassy Ecosystem

**Critical**: All Embassy crates MUST use the same version to avoid type incompatibility.

```toml
embassy-executor = { workspace = true }
embassy-time = { workspace = true }
embassy-sync = { workspace = true }
embassy-net = { workspace = true }
embassy-futures = { workspace = true }
```

### ESP Platform Crates

These require chip-specific features:

```toml
esp-hal = { workspace = true }      # Needs chip feature
esp-wifi = { workspace = true }     # Needs chip feature (if WiFi available)
esp-storage = { workspace = true }  # May need chip feature for flash layout
esp-alloc = { workspace = true }
esp-backtrace = { workspace = true }
esp-println = { workspace = true }
```

### Embedded HAL Traits

Standard embedded-hal traits (usually no chip features needed):

```toml
embedded-hal = { workspace = true }
embedded-hal-async = { workspace = true }
embedded-storage = { workspace = true }
```

## Generated Project Structure

When Python generates a project, it creates:

```toml
[package]
name = "my-device"
version = "0.1.0"
edition = "2024"

[dependencies]
esphome-core = { path = "../embhome/core", features = ["esp32c3"] }
esphome-wifi = { path = "../embhome/components/wifi", features = ["esp32c3"] }
# ... other components with features = ["esp32c3"]

[features]
# Optionally define here too for clarity
esp32c3 = ["esphome-core/esp32c3", "esphome-wifi/esp32c3"]

[[bin]]
name = "my-device"
path = "src/main.rs"
```

The feature propagates:
1. User builds with `--features esp32c3` or it's in `Cargo.toml`
2. All components receive `features = ["esp32c3"]`
3. Components forward to `esp-hal/esp32c3`, `esp-wifi/esp32c3`, etc.
4. Platform crates compile correct code for ESP32-C3

## Verifying Correct Configuration

### Check Dependency Versions

```bash
cd /embhome
cargo tree --duplicates
```

Should show NO duplicates. If you see duplicates, a component is not using workspace dependencies.

### Check Feature Propagation

```bash
cd /embhome
cargo tree --features esp32c3 --edges features
```

Should show features flowing from root to all platform crates.

### Build Test

```bash
cd /embhome/components/wifi
cargo build --features esp32c3
```

Should compile without errors. If you get "no chip feature selected", feature forwarding is broken.

## Troubleshooting

### Problem: "Multiple versions of X found"

**Cause**: A component is not using workspace dependencies.

**Fix**: Change `dependency = "1.0"` to `dependency = { workspace = true }`

### Problem: "No chip feature selected" error from esp-hal

**Cause**: Feature is not being forwarded correctly.

**Fix**:
1. Check component's `[features]` section forwards to esp-hal
2. Check build command includes feature: `cargo build --features esp32c3`
3. Check generated project's `Cargo.toml` enables feature

### Problem: "Type X from embassy-time 0.3.2 is not compatible with embassy-time 0.5.0"

**Cause**: Multiple versions of Embassy crates in use.

**Fix**:
1. Run `cargo tree --duplicates` to find which crate is using old version
2. Update that crate's `Cargo.toml` to use `{ workspace = true }`

### Problem: Build fails with linker errors about WiFi

**Cause**: WiFi component needs chip feature but didn't receive it.

**Fix**: Add WiFi component to your feature forwarding chain:

```toml
esp32c3 = ["esphome-core/esp32c3", "esphome-wifi/esp32c3"]
```

## Best Practices

### DO:

1. ✅ Always use `{ workspace = true }` for dependencies
2. ✅ Forward chip features to all dependencies that need them
3. ✅ Keep workspace dependency versions in sync
4. ✅ Use `default = []` for component features
5. ✅ Run `cargo tree --duplicates` regularly

### DON'T:

1. ❌ Specify version in component crates
2. ❌ Use `default-features = true` for platform crates
3. ❌ Forget to forward chip features
4. ❌ Add features to workspace dependencies (do it in components)
5. ❌ Mix versions of Embassy crates

## Adding New Chip Support

To add a new chip (e.g., esp32c7):

1. Add to workspace metadata in `/embhome/Cargo.toml`:
```toml
[workspace.metadata.chip-features]
chips = [..., "esp32c7"]
esp32c7 = ["esp-hal/esp32c7", "esp-wifi/esp32c7"]
```

2. Add to esphome-core features:
```toml
[features]
esp32c7 = []
```

3. Add to all component features:
```toml
[features]
esp32c7 = ["esphome-core/esp32c7", ...]
```

4. Update Python code generator to support new chip

## Component Dependency Matrix

| Component      | esp-hal | esp-wifi | embassy-net | embassy-time | Notes |
|---------------|---------|----------|-------------|--------------|-------|
| esphome-core  | ❌      | ❌       | ❌          | ✅           | No HAL deps |
| esphome-hal   | ✅      | ❌       | ❌          | ❌           | Wraps esp-hal |
| esphome-gpio  | ❌      | ❌       | ❌          | ❌           | Via esphome-hal |
| esphome-wifi  | ✅      | ✅       | ✅          | ✅           | Needs chip feature |
| esphome-api   | ❌      | ❌       | ✅          | ✅           | Network only |
| esphome-ota   | ✅      | ❌       | ✅          | ✅           | Needs storage |
| esphome-sensor| ❌      | ❌       | ❌          | ❌           | Pure logic |
| esphome-uptime| ❌      | ❌       | ❌          | ✅           | Timer only |

Legend:
- ✅ = Direct dependency (must forward chip features if applicable)
- ❌ = No dependency

## References

- [Cargo Workspaces](https://doc.rust-lang.org/cargo/reference/workspaces.html)
- [Cargo Features](https://doc.rust-lang.org/cargo/reference/features.html)
- [esp-hal Feature Flags](https://github.com/esp-rs/esp-hal)
- [Embassy Documentation](https://embassy.dev/)
