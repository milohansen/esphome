#!/bin/bash
# Test Rust migration code generation

test_configs=(
    "tests/configs/basic_gpio.yaml"
    "tests/configs/i2c_sensors.yaml"
    "tests/configs/mixed_components.yaml"
)

for config in "${test_configs[@]}"; do
    echo "Testing generation for: $config"

    # Run esphome compile with --rust and --only-generate
    python3 -m esphome compile --rust --only-generate "$config"

    if [ $? -eq 0 ]; then
        echo "✓ $config generation successful"

        # Verify generated files exist
        name=$(basename "$config" .yaml)
        # ESPHome creates .esphome in the same directory as the config file
        config_dir=$(dirname "$config")
        build_dir="$config_dir/.esphome/build/$name/rust"
        files=("bridge.cpp" "bridge.rs" "main.rs" "Cargo.toml" "build.rs")

        for file in "${files[@]}"; do
            if [ -f "$build_dir/$file" ]; then
                echo "  ✓ $file exists"
            else
                echo "  ✗ $file missing"
                exit 1
            fi
        done
    else
        echo "✗ $config generation failed"
        exit 1
    fi
done

echo "All generation tests passed"
