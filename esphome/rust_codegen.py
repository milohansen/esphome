import os
from pathlib import Path

from esphome.const import CONF_NAME, CONF_PASSWORD, CONF_SSID
from esphome.rust_generator import RustDependency, RustFunction, RustGenerator


def get_pin_number(pin_config):
    # This assumes pin_config has been normalized by standard validation
    if isinstance(pin_config, dict):
        return pin_config.get("number")
    return pin_config


def generate_gpio_switch(gen: RustGenerator, config, index):
    # ... existing implementation ...
    switch_id = config.get("id", f"switch_{index}")
    pin_num = get_pin_number(config["pin"])
    inverted = config.get("inverted", False)
    initial_state = False  # TODO: Get from config

    # Generate task function
    task_name = f"{switch_id}_task"

    body = f"""
    use embassy_sync::channel::Channel;
    use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;
    use esphome_core::{{Component, ActorAddress}};
    use esphome_gpio::switch::{{GpioSwitch, GpioSwitchConfig, SwitchCommand}};

    static MAILBOX: Channel<CriticalSectionRawMutex, SwitchCommand, 8> = Channel::new();

    let mut comp = GpioSwitch::new("{switch_id}");
    let config = GpioSwitchConfig {{
        pin,
        initial_state: {str(initial_state).lower()},
        inverted: {str(inverted).lower()},
    }};

    comp.setup(config).await.expect("Setup failed");
    comp.run(MAILBOX.receiver()).await;
    """

    func = RustFunction(
        name=task_name,
        body=body,
        is_async=True,
        attributes=["#[embassy_executor::task]"],
        args=[f"pin: esp_hal::gpio::GpioPin<{pin_num}>"],
    )

    gen.add_function(func)

    # Add spawn call to main
    gen.add_component_spawn(
        f'spawner.spawn({task_name}(io.pins.gpio{pin_num})).expect("Failed to spawn {switch_id}");'
    )


def generate_gpio_binary_sensor(gen: RustGenerator, config, index):
    # ... existing implementation ...
    sensor_id = config.get("id", f"binary_sensor_{index}")
    pin_num = get_pin_number(config["pin"])
    inverted = config.get("inverted", False)
    pullup = config.get("pullup", False)
    pulldown = config.get("pulldown", False)

    # Generate task function
    task_name = f"{sensor_id}_task"

    body = f"""
    use embassy_sync::channel::Channel;
    use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;
    use esphome_core::{{Component, ActorAddress}};
    use esphome_gpio::binary_sensor::{{GpioBinarySensor, GpioBinarySensorConfig, BinarySensorEvent}};

    static MAILBOX: Channel<CriticalSectionRawMutex, (), 8> = Channel::new();

    let mut comp = GpioBinarySensor::new("{sensor_id}");
    let config = GpioBinarySensorConfig {{
        pin,
        inverted: {str(inverted).lower()},
        pullup: {str(pullup).lower()},
        pulldown: {str(pulldown).lower()},
    }};

    comp.setup(config).await.expect("Setup failed");
    comp.run(MAILBOX.receiver()).await;
    """

    func = RustFunction(
        name=task_name,
        body=body,
        is_async=True,
        attributes=["#[embassy_executor::task]"],
        args=[f"pin: esp_hal::gpio::GpioPin<{pin_num}>"],
    )

    gen.add_function(func)

    # Add spawn call to main
    gen.add_component_spawn(
        f'spawner.spawn({task_name}(io.pins.gpio{pin_num})).expect("Failed to spawn {sensor_id}");'
    )


def generate_uptime_sensor(gen: RustGenerator, config, index):
    sensor_id = config.get("id", f"uptime_sensor_{index}")
    update_interval = config.get("update_interval", "60s")
    # Simple duration parsing (placeholder)
    # TODO: Use esphome's cv.TimePeriod normalized value
    seconds = 60
    if isinstance(update_interval, str) and update_interval.endswith("s"):
        seconds = int(update_interval[:-1])

    task_name = f"{sensor_id}_task"

    body = f"""
    use embassy_sync::channel::Channel;
    use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;
    use embassy_time::Duration;
    use esphome_core::Component;
    use esphome_uptime::UptimeSensor;

    static MAILBOX: Channel<CriticalSectionRawMutex, (), 8> = Channel::new();

    let mut comp = UptimeSensor::new("{sensor_id}");
    comp.setup(Duration::from_secs({seconds})).await.expect("Setup failed");
    comp.run(MAILBOX.receiver()).await;
    """

    func = RustFunction(
        name=task_name,
        body=body,
        is_async=True,
        attributes=["#[embassy_executor::task]"],
    )

    gen.add_function(func)
    gen.add_component_spawn(
        f'spawner.spawn({task_name}()).expect("Failed to spawn {sensor_id}");'
    )


def generate_rust_project(config, output_dir: Path):
    gen = RustGenerator()

    # Determine chip/features
    chip = "esp32"
    board = config["esphome"].get("board", "esp32")
    board_parts = board.split("-")
    if board_parts[0] == "esp32" and board_parts[1] in ["c3", "s2", "s3"]:
        chip = f"esp32{board_parts[1]}"

    # Adjust paths to point to the repo root from build dir
    # rust_root = Path(os.getcwd()) / "esphome/rust"
    rust_root = Path(os.getcwd()) / "embhome"

    # Core Dependencies
    gen.add_dependency(
        RustDependency("esphome-core", "0.1.0", path=str(rust_root / "core"))
    )
    gen.add_dependency(
        RustDependency("esphome-hal", "0.1.0", path=str(rust_root / "hal"))
    )
    gen.add_dependency(
        RustDependency("esphome-config", "0.1.0", path=str(rust_root / "config"))
    )

    # HAL Dependencies
    # TODO: adjust psram feature based on board capabilities
    # PSRAM is quad by default, can be configured to octal via ESP_HAL_CONFIG_PSRAM_MODE
    gen.add_dependency(
        RustDependency("esp-hal", "1.0", features=[chip, "log-04", "psram", "unstable"])
    )

    # TODO: enable "internal-heap-stats" feature based on config debug level
    gen.add_dependency(RustDependency("esp-alloc", "0.9", features=[chip]))

    gen.add_dependency(
        # TODO: conditionally add rtos-trace feature based on config debug level
        RustDependency(
            "esp-rtos",
            "0.2.0",
            features=[chip, "embassy", "log-04", "esp-alloc", "esp-radio"],
        )
    )

    # executor_features = ["task-arena-size-32768", "executor-thread", "arch-riscv32"]
    # if chip == "esp32c3":
    #     executor_features.append("arch-riscv32")
    # else:
    #     executor_features.append("arch-xtensa")

    gen.add_dependency(
        # Note: Do not enable any `arch-*` features here, they are selected by esp-rtos
        # see: https://docs.espressif.com/projects/rust/esp-rtos/0.2.0/esp32c3/esp_rtos/index.html#setup
        RustDependency("embassy-executor", "0.9.1", features=["executor-thread", "log"])
    )
    gen.add_dependency(RustDependency("log", "0.4"))
    gen.add_dependency(
        RustDependency(
            "esp-backtrace",
            "0.14.2",
            features=[chip, "panic-handler", "println"],
        )
    )
    gen.add_dependency(RustDependency("static_cell", "2.1.0"))

    # App Setup
    app_name = config["esphome"][CONF_NAME]

    gen.add_main_code(
        f'let mut app = Application::new("{app_name}", Platform::{chip.capitalize()});'
    )
    gen.add_main_code('app.init().await.expect("App init failed");')
    gen.add_main_code(
        "let io = esp_hal::gpio::IO::new(peripherals.GPIO, peripherals.IO_MUX);"
    )

    radio_features: list[str] | None = None
    # WiFi Setup
    # stack_var = "stack"
    if "wifi" in config:
        wifi_conf = config["wifi"]
        gen.add_dependency(
            RustDependency(
                "esphome-wifi",
                "0.1.0",
                path=str(rust_root / "components/wifi"),
                features=[chip],
            )
        )
        radio_features = ["wifi"]
        gen.add_dependency(RustDependency("esp-alloc", "0.5.0"))
        gen.add_dependency(
            RustDependency(
                "embassy-net",
                "0.6.0",
                features=["tcp", "udp", "dhcpv4", "medium-ethernet"],
            )
        )

        gen.add_global_macro("use esp_alloc::heap_allocator;")
        gen.add_global_macro("heap_allocator!(72 * 1024);")

        gen.add_main_code(
            "let timer_group1 = TimerGroup::new(peripherals.TIMG1, &clocks);"
        )
        gen.add_main_code(
            """
    let init = esp_wifi::init(
        timer_group1.timer0,
        esp_hal::rng::Rng::new(peripherals.RNG),
        peripherals.RADIO_CLK,
        &clocks,
    ).unwrap();
        """
        )

        gen.add_main_code(
            """
    let (wifi_interface, controller) = esp_wifi::wifi::new_with_mode(
        &init,
        peripherals.WIFI,
        esp_wifi::wifi::WifiStaDevice,
    ).unwrap();
        """
        )

        # Static allocations
        gen.add_main_code(
            "static WIFI_RESOURCES: static_cell::StaticCell<esphome_wifi::WifiResources> = static_cell::StaticCell::new();"
        )
        gen.add_main_code(
            "let wifi_resources = WIFI_RESOURCES.init(esphome_wifi::WifiResources::new());"
        )

        gen.add_main_code(
            """
    let config = embassy_net::Config::dhcpv4(Default::default());
    let seed = 1234;

    let (stack, runner) = embassy_net::new(
        wifi_interface,
        config,
        &mut wifi_resources.stack_resources,
        seed
    );
        """
        )

        gen.add_main_code(
            "static STACK: static_cell::StaticCell<esphome_wifi::WifiStack> = static_cell::StaticCell::new();"
        )
        gen.add_main_code("let stack = STACK.init(stack);")

        gen.add_component_spawn(
            "spawner.spawn(esphome_wifi::net_task(stack)).unwrap();"
        )

        networks = wifi_conf.get("networks", [])
        ssid = ""
        password = ""
        if networks:
            first_net = networks[0]
            ssid = first_net.get(CONF_SSID, "")
            password = first_net.get(CONF_PASSWORD, "")
        elif CONF_SSID in wifi_conf:
            ssid = wifi_conf.get(CONF_SSID, "")
            password = wifi_conf.get(CONF_PASSWORD, "")

        gen.add_main_code(
            f"""
    let wifi_config = esphome_config::WifiConfig {{
        ssid: \"{ssid}\".to_string(),
        password: \"{password}\".to_string(),
        fast_connect: false,
    }};
        """
        )
        gen.add_component_spawn(
            "spawner.spawn(esphome_wifi::connection_task(controller, wifi_config)).unwrap();"
        )

    if radio_features:
        gen.add_dependency(
            RustDependency("esp-radio", "0.17.0", features=[*radio_features, "log-04"])
        )
        gen.add_dependency(RustDependency("esp-radio-rtos-driver", "0.2.0"))

    # API Setup
    if "api" in config:
        gen.add_dependency(
            RustDependency(
                "esphome-api", "0.1.0", path=str(rust_root / "components/api")
            )
        )
        gen.add_dependency(
            RustDependency(
                "prost", "0.14.3", default_features=False, features=["alloc"]
            )
        )
        gen.add_component_spawn(
            "spawner.spawn(esphome_api::api_server(stack)).unwrap();"
        )

    # OTA Setup
    if "ota" in config:
        gen.add_dependency(
            RustDependency(
                "esphome-ota", "0.1.0", path=str(rust_root / "components/ota")
            )
        )
        gen.add_component_spawn(
            "spawner.spawn(esphome_ota::ota_server(stack)).unwrap();"
        )

    # Components
    if "switch" in config:
        gen.add_dependency(
            RustDependency(
                "esphome-gpio", "0.1.0", path=str(rust_root / "components/gpio")
            )
        )
        for i, conf in enumerate(config["switch"]):
            if conf.get("platform") == "gpio":
                generate_gpio_switch(gen, conf, i)

        if "binary_sensor" in config and "esphome-gpio" not in [
            d.name for d in gen.dependencies
        ]:
            gen.add_dependency(
                RustDependency(
                    "esphome-gpio", "0.1.0", path=str(rust_root / "components/gpio")
                )
            )
        for i, conf in enumerate(config["binary_sensor"]):
            if conf.get("platform") == "gpio":
                generate_gpio_binary_sensor(gen, conf, i)

    if "sensor" in config:
        for i, conf in enumerate(config["sensor"]):
            if conf.get("platform") == "uptime":
                if "esphome-uptime" not in [d.name for d in gen.dependencies]:
                    gen.add_dependency(
                        RustDependency(
                            "esphome-uptime",
                            "0.1.0",
                            path=str(rust_root / "components/uptime"),
                        )
                    )
                    gen.add_dependency(
                        RustDependency(
                            "esphome-sensor",
                            "0.1.0",
                            path=str(rust_root / "components/sensor"),
                        )
                    )
                generate_uptime_sensor(gen, conf, i)

    # Write Output
    src_dir = output_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "Cargo.toml", "w") as f:
        f.write(gen.generate_cargo_toml())

    with open(src_dir / "main.rs", "w") as f:
        f.write(gen.generate_main_rs())

    # .cargo/config.toml
    cargo_conf_dir = output_dir / ".cargo"
    cargo_conf_dir.mkdir(exist_ok=True)

    target = "xtensa-esp32-none-elf"
    if chip == "esp32c3":
        target = "riscv32imc-unknown-none-elf"

    with open(cargo_conf_dir / "config.toml", "w") as f:
        f.write(
            f'[build]\ntarget = "{target}"\n\n[target.{target}]\nrunner = "espflash flash --monitor"\n'
        )
