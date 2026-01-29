# Rust Component Code Generation Architecture

## Problem

Currently, all Rust code generation is centralized in `esphome/rust_codegen.py`, which contains hardcoded initialization logic for each component (WiFi, API, GPIO, etc.). This creates several issues:

1. **Tight coupling**: Adding a new component requires modifying `rust_codegen.py`
2. **Poor separation of concerns**: WiFi-specific code is in a central file
3. **Difficult maintenance**: Component maintainers can't own their code generation
4. **Inconsistent with C++**: C++ components use `__init__.py` files for code generation

## Current State

Example from `esphome/rust_codegen.py` (lines 246-299):

```python
# WiFi Setup - HARDCODED IN CENTRAL FILE
if "wifi" in config:
    wifi_conf = config["wifi"]
    gen.add_dependency(
        RustDependency("esphome-wifi", "0.1.0",
                      path=str(rust_root / "components/wifi"),
                      features=[chip])
    )
    gen.add_dependency(
        RustDependency("embassy-net", "0.6.0",
                      features=["tcp", "udp", "dhcpv4", "medium-ethernet"])
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
    # ... 50+ more lines of WiFi-specific code
```

This pattern repeats for every component!

## Proposed Solution

### Architecture Overview

```
embhome/
├── components/
│   ├── wifi/
│   │   ├── __init__.py          # NEW: Code generation hooks
│   │   ├── src/
│   │   │   └── lib.rs            # Rust implementation
│   │   └── Cargo.toml
│   ├── api/
│   │   ├── __init__.py          # NEW: Code generation hooks
│   │   ├── src/
│   │   └── Cargo.toml
│   └── gpio/
│       ├── __init__.py          # NEW: Code generation hooks
│       ├── src/
│       └── Cargo.toml
└── core/
    └── rust_component.py        # NEW: Base class for Rust components
```

### Base Class: `RustComponent`

Create `/embhome/core/rust_component.py`:

```python
"""
Base class for Rust component code generation.
Similar pattern to C++ components but for Rust.
"""

from dataclasses import dataclass
from typing import Any, Optional
from pathlib import Path
from esphome.rust_generator import RustGenerator, RustDependency


@dataclass
class RustComponentConfig:
    """Configuration passed to component during code generation"""
    chip: str
    config: dict[str, Any]
    rust_root: Path


class RustComponent:
    """
    Base class for Rust component code generation.

    Components should subclass this and implement the hooks they need.
    """

    def __init__(self, component_name: str):
        self.component_name = component_name

    def get_dependencies(
        self,
        gen: RustGenerator,
        config: RustComponentConfig
    ) -> list[RustDependency]:
        """
        Return list of Rust dependencies this component needs.

        Called early in code generation to build dependency list.
        """
        return []

    def add_global_code(
        self,
        gen: RustGenerator,
        config: RustComponentConfig
    ) -> None:
        """
        Add global macros, statics, and top-level code.

        Called before main() is generated.
        """
        pass

    def add_setup_code(
        self,
        gen: RustGenerator,
        config: RustComponentConfig
    ) -> None:
        """
        Add code to main() for component initialization.

        Called during main() generation, before component spawning.
        """
        pass

    def add_spawn_code(
        self,
        gen: RustGenerator,
        config: RustComponentConfig
    ) -> None:
        """
        Add component task spawning code.

        Called at the end of main() for spawning component tasks.
        """
        pass

    def requires_heap(self) -> bool:
        """Return True if component needs heap allocator"""
        return False

    def heap_size(self) -> int:
        """Return required heap size in KB"""
        return 0


# Component registry
_RUST_COMPONENTS: dict[str, RustComponent] = {}


def register_rust_component(name: str, component: RustComponent) -> None:
    """Register a Rust component for code generation"""
    _RUST_COMPONENTS[name] = component


def get_rust_component(name: str) -> Optional[RustComponent]:
    """Get a registered Rust component"""
    return _RUST_COMPONENTS.get(name)


def get_all_rust_components() -> dict[str, RustComponent]:
    """Get all registered Rust components"""
    return _RUST_COMPONENTS
```

### Example: WiFi Component

Create `/embhome/components/wifi/__init__.py`:

```python
"""
WiFi component code generation for Rust.

This module provides code generation hooks for the WiFi component,
allowing it to inject dependencies and initialization code into
generated projects.
"""

from esphome.rust_generator import RustGenerator, RustDependency
from embhome.core.rust_component import (
    RustComponent,
    RustComponentConfig,
    register_rust_component
)


class WifiComponent(RustComponent):
    """WiFi component code generation"""

    def __init__(self):
        super().__init__("wifi")

    def get_dependencies(
        self,
        gen: RustGenerator,
        config: RustComponentConfig
    ) -> list[RustDependency]:
        """Add WiFi-specific dependencies"""
        rust_root = config.rust_root
        chip = config.chip

        return [
            RustDependency(
                "esphome-wifi",
                "0.1.0",
                path=str(rust_root / "components/wifi"),
                features=[chip]
            ),
            RustDependency(
                "embassy-net",
                "0.6.0",
                features=["tcp", "udp", "dhcpv4", "medium-ethernet"]
            ),
        ]

    def requires_heap(self) -> bool:
        return True

    def heap_size(self) -> int:
        return 72  # 72 KB for WiFi stack

    def add_global_code(
        self,
        gen: RustGenerator,
        config: RustComponentConfig
    ) -> None:
        """Add heap allocator for WiFi"""
        heap_kb = self.heap_size()
        gen.add_global_macro("use esp_alloc::heap_allocator;")
        gen.add_global_macro(f"heap_allocator!({heap_kb} * 1024);")

    def add_setup_code(
        self,
        gen: RustGenerator,
        config: RustComponentConfig
    ) -> None:
        """Add WiFi initialization code to main()"""

        # Timer group for WiFi
        gen.add_main_code(
            "let timer_group1 = TimerGroup::new(peripherals.TIMG1, &clocks);"
        )

        # Initialize esp-wifi
        gen.add_main_code("""
    let init = esp_wifi::init(
        timer_group1.timer0,
        esp_hal::rng::Rng::new(peripherals.RNG),
        peripherals.RADIO_CLK,
        &clocks,
    ).unwrap();
        """)

        # Create WiFi interface
        gen.add_main_code("""
    let (wifi_interface, controller) = esp_wifi::wifi::new_with_mode(
        &init,
        peripherals.WIFI,
        esp_wifi::wifi::WifiStaDevice,
    ).unwrap();
        """)

        # Static allocations for WiFi resources
        gen.add_main_code(
            "static WIFI_RESOURCES: static_cell::StaticCell<esphome_wifi::WifiResources> = "
            "static_cell::StaticCell::new();"
        )
        gen.add_main_code(
            "let wifi_resources = WIFI_RESOURCES.init(esphome_wifi::WifiResources::new());"
        )

        # Create network stack
        gen.add_main_code("""
    let config = embassy_net::Config::dhcpv4(Default::default());
    let seed = 1234;

    let (stack, runner) = embassy_net::new(
        wifi_interface,
        config,
        &mut wifi_resources.stack_resources,
        seed
    );
        """)

        # Static stack reference
        gen.add_main_code(
            "static STACK: static_cell::StaticCell<esphome_wifi::WifiStack> = "
            "static_cell::StaticCell::new();"
        )
        gen.add_main_code("let stack = STACK.init(stack);")

    def add_spawn_code(
        self,
        gen: RustGenerator,
        config: RustComponentConfig
    ) -> None:
        """Spawn WiFi network task"""
        gen.add_component_spawn(
            "spawner.spawn(esphome_wifi::net_task(stack)).unwrap();"
        )

        # Get WiFi credentials from config
        wifi_config = config.config.get("wifi", {})
        ssid = wifi_config.get("ssid", "")
        password = wifi_config.get("password", "")

        # Spawn WiFi manager task
        gen.add_component_spawn(
            f'spawner.spawn(esphome_wifi::wifi_task(controller, stack, '
            f'"{ssid}", "{password}")).unwrap();'
        )


# Register the component
register_rust_component("wifi", WifiComponent())
```

### Example: GPIO Component

Create `/embhome/components/gpio/__init__.py`:

```python
"""
GPIO component code generation for Rust.
"""

from esphome.rust_generator import RustGenerator, RustDependency, RustFunction
from embhome.core.rust_component import (
    RustComponent,
    RustComponentConfig,
    register_rust_component
)


class GpioComponent(RustComponent):
    """GPIO component code generation"""

    def __init__(self):
        super().__init__("gpio")

    def get_dependencies(
        self,
        gen: RustGenerator,
        config: RustComponentConfig
    ) -> list[RustDependency]:
        """Add GPIO component dependency"""
        rust_root = config.rust_root

        return [
            RustDependency(
                "esphome-gpio",
                "0.1.0",
                path=str(rust_root / "components/gpio")
            ),
        ]

    def generate_switch(
        self,
        gen: RustGenerator,
        config: RustComponentConfig,
        switch_config: dict,
        index: int
    ) -> None:
        """Generate code for a GPIO switch"""
        switch_id = switch_config.get("id", f"switch_{index}")
        pin_num = self._get_pin_number(switch_config["pin"])
        inverted = switch_config.get("inverted", False)
        initial_state = False

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
        gen.add_component_spawn(
            f'spawner.spawn({task_name}(io.pins.gpio{pin_num}))'
            f'.expect("Failed to spawn {switch_id}");'
        )

    def _get_pin_number(self, pin_config):
        """Extract pin number from config"""
        if isinstance(pin_config, dict):
            return pin_config.get("number")
        return pin_config


# Register the component
register_rust_component("gpio", GpioComponent())
```

### Updated `rust_codegen.py`

```python
"""
Rust code generation - now using component hooks.
"""

from pathlib import Path
from esphome.rust_generator import RustGenerator, RustDependency
from embhome.core.rust_component import (
    get_rust_component,
    RustComponentConfig
)


def generate_rust_project(config, output_dir: Path):
    gen = RustGenerator()

    # Determine chip
    chip = "esp32"
    board = config["esphome"].get("board", "esp32")
    board_parts = board.split("-")
    if board_parts[0] == "esp32" and board_parts[1] in ["c3", "s2", "s3"]:
        chip = f"esp32{board_parts[1]}"

    rust_root = Path(os.getcwd()) / "embhome"

    # Create component config
    component_config = RustComponentConfig(
        chip=chip,
        config=config,
        rust_root=rust_root
    )

    # Always add core dependencies
    gen.add_dependency(
        RustDependency("esphome-core", "0.1.0", path=str(rust_root / "core"))
    )
    gen.add_dependency(
        RustDependency("esphome-hal", "0.1.0", path=str(rust_root / "hal"))
    )

    # Add platform dependencies
    gen.add_dependency(
        RustDependency("esp-hal", "1.0", features=[chip, "log-04", "psram", "unstable"])
    )
    gen.add_dependency(RustDependency("esp-alloc", "0.9", features=[chip]))
    # ... other platform deps

    # ============================================================
    # NEW: Component-driven code generation
    # ============================================================

    # Phase 1: Collect dependencies from all active components
    for component_name in ["wifi", "api", "ota", "gpio"]:
        if component_name in config:
            component = get_rust_component(component_name)
            if component:
                deps = component.get_dependencies(gen, component_config)
                for dep in deps:
                    gen.add_dependency(dep)

    # Phase 2: Add global code (heap allocator, statics, etc.)
    for component_name in ["wifi", "api", "ota", "gpio"]:
        if component_name in config:
            component = get_rust_component(component_name)
            if component:
                component.add_global_code(gen, component_config)

    # App initialization (core, always present)
    app_name = config["esphome"]["name"]
    gen.add_main_code(
        f'let mut app = Application::new("{app_name}", Platform::{chip.capitalize()});'
    )
    gen.add_main_code('app.init().await.expect("App init failed");')
    gen.add_main_code(
        "let io = esp_hal::gpio::IO::new(peripherals.GPIO, peripherals.IO_MUX);"
    )

    # Phase 3: Add component setup code
    for component_name in ["wifi", "api", "ota", "gpio"]:
        if component_name in config:
            component = get_rust_component(component_name)
            if component:
                component.add_setup_code(gen, component_config)

    # Phase 4: Spawn component tasks
    for component_name in ["wifi", "api", "ota", "gpio"]:
        if component_name in config:
            component = get_rust_component(component_name)
            if component:
                component.add_spawn_code(gen, component_config)

    # Generate the actual Rust project files
    gen.write_to_disk(output_dir)
```

## Benefits

### 1. **Separation of Concerns**
- WiFi code lives in `/embhome/components/wifi/__init__.py`
- GPIO code lives in `/embhome/components/gpio/__init__.py`
- Central file only orchestrates component registration

### 2. **Component Ownership**
- Component maintainers own their code generation logic
- Changes to WiFi initialization don't touch central file
- Each component can be developed independently

### 3. **Consistency with C++**
- Follows same pattern as C++ components
- Developers familiar with C++ components understand Rust components
- Easier onboarding for contributors

### 4. **Extensibility**
- Adding new components doesn't require modifying `rust_codegen.py`
- Third-party components can register themselves
- Component marketplace becomes possible

### 5. **Testability**
- Each component can be tested in isolation
- Mock `RustGenerator` for unit tests
- Clearer separation of concerns

## Migration Path

### Phase 1: Create Infrastructure
1. Create `/embhome/core/rust_component.py` base class
2. Update `RustGenerator` to support component hooks
3. Add component registration system

### Phase 2: Migrate One Component
1. Start with WiFi (most complex)
2. Create `/embhome/components/wifi/__init__.py`
3. Move all WiFi code from `rust_codegen.py`
4. Test thoroughly

### Phase 3: Migrate Remaining Components
1. GPIO (switches, binary sensors)
2. API
3. OTA
4. Sensors

### Phase 4: Cleanup
1. Remove hardcoded component logic from `rust_codegen.py`
2. Update documentation
3. Add examples for third-party components

## Example: Adding a New Component

With the new architecture, adding a component is self-contained:

```python
# /embhome/components/my_component/__init__.py

from embhome.core.rust_component import RustComponent, register_rust_component

class MyComponent(RustComponent):
    def __init__(self):
        super().__init__("my_component")

    def get_dependencies(self, gen, config):
        return [
            RustDependency("my-crate", "1.0.0")
        ]

    def add_setup_code(self, gen, config):
        gen.add_main_code("// My component setup")

register_rust_component("my_component", MyComponent())
```

That's it! No changes to `rust_codegen.py` required.

## Comparison: Before vs After

### Before (Current)
```
rust_codegen.py (500+ lines)
├── WiFi setup (50 lines)
├── API setup (40 lines)
├── OTA setup (30 lines)
├── GPIO setup (80 lines)
└── ... all components hardcoded
```

### After (Proposed)
```
rust_codegen.py (150 lines)
└── Component orchestration only

embhome/components/wifi/__init__.py (100 lines)
└── WiFi-specific code

embhome/components/api/__init__.py (80 lines)
└── API-specific code

embhome/components/gpio/__init__.py (100 lines)
└── GPIO-specific code
```

## Conclusion

This architecture:
- ✅ Separates component concerns
- ✅ Enables component ownership
- ✅ Matches C++ component patterns
- ✅ Supports extensibility
- ✅ Improves testability
- ✅ Reduces coupling

**Recommendation**: Implement this architecture to align Rust component code generation with ESPHome's established C++ patterns.
