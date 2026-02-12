# Testing ESPHome Rust Migration

## Compilation Tests

A suite of test configurations is provided to ensure the generator produces valid code for various scenarios.

Run the compilation tests:
```bash
./tests/compilation_tests/run_all.sh
```

## Manual Smoke Test

To verify that the generated firmware actually runs on hardware:

1. Connect an ESP32 board.
2. Run the smoke test configuration:
   ```bash
   esphome run --rust tests/configs/smoke_test.yaml
   ```
3. Verify the following in the serial logs:
   - "Embassy executor started" message.
   - Successful initialization of components.
   - No "panic" messages.
   - Device runs for at least 5 minutes without resetting.

## Integration Tests

If you have real hardware peripherals:

1. **GPIO Loopback**: Connect GPIO12 to GPIO13. Run `tests/configs/gpio_loopback.yaml` and verify that pressing the button toggles the LED.
2. **I2C Sensor**: Connect a BMP280 to GPIO21/22. Run `tests/configs/i2c_sensor.yaml` and verify sensor readings are appearing in logs.
