# Running the ESPHome Rust/Embassy Migration Project

This document provides instructions for setting up and running the hybrid Rust/Embassy ESPHome environment.

## Prerequisites

To build and run this project, you need the following tools installed:

1.  **Rust Toolchain**:
    *   Install Rust via [rustup](https://rustup.rs/).
    *   Add the RISC-V target for ESP32-C3:
        ```bash
        rustup target add riscv32imc-unknown-none-elf
        ```
    *   Install `espflash`:
        ```bash
        cargo install espflash
        ```

2.  **Python & ESPHome**:
    *   Python 3.9 or newer.
    *   Install ESPHome dependencies:
        ```bash
        pip install -r requirements.txt
        ```

3.  **C++ Toolchain**:
    *   PlatformIO (usually managed by ESPHome) or a standalone ESP-IDF installation.

## Project Structure

*   `/embhome`: The Rust project root.
    *   `src/main.rs`: The async entry point and supervisor.
    *   `src/legacy_wrapper.rs`: Adapter for running C++ components.
    *   `src/registry.rs`: Component ID registry for FFI resolution.
    *   `build.rs`: Cargo build script for linking `libesphome.a` and generating bindings.

## How to Run

### 1. Configuration

Create an ESPHome YAML configuration and target the ESP32-C3 platform. Native Rust components should be flagged in their implementation (see `esphome/components/rust_test` for an example).

```yaml
esphome:
  name: test-rust

esp32:
  board: esp32-c3-devkitm-1
  variant: esp32c3
  framework:
    type: esp-idf

rust_test:
  id: my_rust_comp

sensor:
  - platform: dht
    pin: 4
    id: my_dht
```

### 2. Generate and Build

Run the ESPHome compilation command. This will trigger the refactored code generator to produce the Rust bridge artifacts.

```bash
python3 -m esphome compile test.yaml
```

ESPHome will now:
1.  Generate `bridge.cpp`, `bridge.rs`, and `main.rs` inside `embhome/`.
2.  Trigger the C++ build to create `libesphome.a`.
3.  Link everything into the final Rust binary via Cargo.

### 3. Manual Rust Build (Optional)

If you wish to build the Rust project manually for debugging:

```bash
cd embhome
cargo build --release
```

Note: This requires `libesphome.a` to be present in the `embhome/` directory.

## Safety and Concurrency

*   **Single-Threaded Constraint**: All `LegacyWrapper` tasks must run on the same thread to prevent data races with global C++ state.
*   **Dual HAL**: Do not assign the same GPIO pins or buses to both a Rust and a C++ component. The code generator will raise a validation error if this happens.
*   **Non-Blocking**: Ensure that C++ `loop()` methods do not contain blocking calls, as they will starve the Embassy executor.
