"""
WiFi component code generation for Rust.

This module provides code generation hooks for the WiFi component,
allowing it to inject dependencies and initialization code into
generated projects.
"""

from pathlib import Path
import sys

# Add embhome to path so we can import rust_component
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from embhome.core.rust_component import (  # noqa: E402
    RustComponent,
    RustComponentConfig,
    register_rust_component,
)

# Constants - imported from esphome when available
try:
    from esphome.const import CONF_PASSWORD, CONF_SSID
except ImportError:
    # Fallback for when running outside ESPHome context
    CONF_SSID = "ssid"
    CONF_PASSWORD = "password"


class WifiComponent(RustComponent):
    """WiFi component code generation"""

    def __init__(self):
        super().__init__("wifi")

    def get_dependencies(self, gen, config: RustComponentConfig) -> list:
        """Add WiFi-specific dependencies"""
        # Import here to avoid circular dependencies
        from esphome.rust_generator import RustDependency

        rust_root = config.rust_root
        chip = config.chip

        return [
            RustDependency(
                "esphome-wifi",
                "0.1.0",
                path=str(rust_root / "components/wifi"),
                features=[chip],
            ),
            RustDependency(
                "embassy-net",
                "0.6.0",
                features=["tcp", "udp", "dhcpv4", "medium-ethernet"],
            ),
            RustDependency("esp-radio", "0.17.0", features=["wifi", "log-04"]),
            RustDependency("esp-radio-rtos-driver", "0.2.0"),
        ]

    def requires_heap(self) -> bool:
        """WiFi requires heap allocator"""
        return True

    def heap_size(self) -> int:
        """WiFi needs 72 KB heap"""
        return 72

    def add_global_code(self, gen, config: RustComponentConfig) -> None:
        """Add heap allocator for WiFi"""
        heap_kb = self.heap_size()
        gen.add_global_macro("use esp_alloc::heap_allocator;")
        gen.add_global_macro(f"heap_allocator!({heap_kb} * 1024);")

    def add_setup_code(self, gen, config: RustComponentConfig) -> None:
        """Add WiFi initialization code to main()"""

        # Timer group for WiFi
        gen.add_main_code(
            "let timer_group1 = TimerGroup::new(peripherals.TIMG1, &clocks);"
        )

        # Initialize esp-wifi
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

        # Create WiFi interface
        gen.add_main_code(
            """
    let (wifi_interface, controller) = esp_wifi::wifi::new_with_mode(
        &init,
        peripherals.WIFI,
        esp_wifi::wifi::WifiStaDevice,
    ).unwrap();
        """
        )

        # Static allocations for WiFi resources
        gen.add_main_code(
            "static WIFI_RESOURCES: static_cell::StaticCell<esphome_wifi::WifiResources> = "
            "static_cell::StaticCell::new();"
        )
        gen.add_main_code(
            "let wifi_resources = WIFI_RESOURCES.init(esphome_wifi::WifiResources::new());"
        )

        # Create network stack
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

        # Static stack reference
        gen.add_main_code(
            "static STACK: static_cell::StaticCell<esphome_wifi::WifiStack> = "
            "static_cell::StaticCell::new();"
        )
        gen.add_main_code("let stack = STACK.init(stack);")

        # Get WiFi credentials from config
        wifi_config = config.config.get("wifi", {})
        ssid = ""
        password = ""

        # Check for networks array first
        networks = wifi_config.get("networks", [])
        if networks:
            first_net = networks[0]
            ssid = first_net.get(CONF_SSID, "")
            password = first_net.get(CONF_PASSWORD, "")
        elif CONF_SSID in wifi_config:
            ssid = wifi_config.get(CONF_SSID, "")
            password = wifi_config.get(CONF_PASSWORD, "")

        # Add WiFi config
        gen.add_main_code(
            f"""
    let wifi_config = esphome_config::WifiConfig {{
        ssid: "{ssid}".to_string(),
        password: "{password}".to_string(),
        fast_connect: false,
    }};
        """
        )

    def add_spawn_code(self, gen, config: RustComponentConfig) -> None:
        """Spawn WiFi network tasks"""
        # Spawn network task
        gen.add_component_spawn(
            "spawner.spawn(esphome_wifi::net_task(stack)).unwrap();"
        )

        # Spawn WiFi connection task
        gen.add_component_spawn(
            "spawner.spawn(esphome_wifi::connection_task(controller, wifi_config)).unwrap();"
        )


# Register the component
register_rust_component("wifi", WifiComponent())
