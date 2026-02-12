# ESPHome Rust Migration Status

## Implemented (Phase 1)

- [x] Hybrid C++/Rust build system integration.
- [x] Rust code generator for bridge artifacts.
- [x] CLI support via `--rust` flag.
- [x] `LegacyWrapper` for running C++ components in Embassy tasks.
- [x] Async I2C Bridge with C++ `Wire` shim.
- [x] Native Rust GPIO Switch.
- [x] Native Rust GPIO Binary Sensor.

## Priority Legacy Components Supported

- [x] DHT (via C++ Bridge)
- [x] BMP280 (via C++ Bridge + I2C shim)

## Planned (Phase 2)

- [ ] SPI Bridge.
- [ ] LEDC (PWM) native Rust implementation.
- [ ] Template components.
- [ ] Support for other ESP32 variants (S2, S3, C3).

## Known Issues

- [x] Static lookup in `bridge.rs`.
- [x] Shadow state synchronization via FFI.
- [x] Factory functions rely on capturing `to_code`.
