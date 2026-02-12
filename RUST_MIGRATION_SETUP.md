# ESPHome Rust Migration Setup Guide

This guide describes how to set up your environment to use the new Rust migration mode in ESPHome.

## Prerequisites

1. **Rust Toolchain for Xtensa**:
   Install `espup` and use it to install the Xtensa toolchain.
   ```bash
   cargo install espup
   espup install
   source $HOME/export-esp.sh
   ```

2. **PlatformIO**:
   Ensure PlatformIO is installed and available in your PATH.
   ```bash
   pip install platformio
   ```

3. **ESPHome**:
   Ensure you are using the version of ESPHome with Rust support enabled.
   ```bash
   pip install -e .
   ```

## Usage

To compile a configuration using the Rust migration mode:
```bash
esphome compile --rust config.yaml
```

To run and flash:
```bash
esphome run --rust config.yaml
```

## Environment Variables

- `ESPHOME_VERBOSE`: Set to `1` for verbose logs.
- `LIBCLANG_PATH`: May be needed for `bindgen` if it cannot find clang.
