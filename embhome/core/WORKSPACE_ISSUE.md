# Workspace Issue: Missing Feature Definition

The `esp32c61` feature is expected by several components (e.g., `esp32`, `i2c`) but is not defined in this crate's `Cargo.toml`.
Either the feature should be added here, or the components should be updated to not use it.
