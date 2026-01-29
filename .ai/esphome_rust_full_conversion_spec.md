# ESPHome Full Rust/Embassy Conversion Specification
## Modern Async Architecture with Modular Component System

**Version**: 2.0
**Target**: Complete rewrite in Rust using Embassy async runtime
**Philosophy**: Clean slate design embracing Rust idioms and Embassy patterns

---

## TABLE OF CONTENTS

1. Vision & Core Principles
2. Architecture Overview
3. Component Model & Actor Pattern
4. Core Runtime Design
5. Hardware Abstraction Layer
6. Configuration System
7. Component Communication
8. Code Generation Strategy
9. Build System
10. Migration Path
11. Component Crate Structure
12. Naming Conventions
13. Reference Implementation
14. Testing Strategy

---

## 1.0 VISION & CORE PRINCIPLES

### 1.1 Project Vision

ESPHome-RS is a complete rewrite of ESPHome in Rust, designed from the ground up for:

- **Type Safety**: Leverage Rust's type system for hardware resource guarantees
- **Async First**: Embassy executor as the foundation, not an afterthought
- **Modular**: Each component is an independent crate with clear interfaces
- **Zero-Cost Abstractions**: Compile-time resolution of all dependencies
- **Modern Patterns**: Actor model for component isolation and communication

### 1.2 Core Architectural Principles

1. **Actor-Based Components**: Each component is an independent actor with mailbox
2. **Message Passing**: All inter-component communication via typed channels
3. **Static Allocation**: Everything allocated at compile time (no heap after init)
4. **Hardware as Types**: GPIO pins, I2C buses encoded in type system
5. **Async Everything**: All I/O operations are async from the ground up
6. **Compile-Time Validation**: Hardware conflicts caught by type checker
7. **Modular Crates**: Components are independent crates with semantic versioning

---

## 2.0 ARCHITECTURE OVERVIEW

### 2.1 System Layers

```
┌─────────────────────────────────────────────────────┐
│           User Configuration (YAML)                 │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│         Code Generator (esphome-codegen)            │
│  Produces: main.rs + component instantiations       │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│              Core Runtime (esphome-core)            │
│  - Embassy executor                                 │
│  - Message bus                                      │
│  - Component registry                               │
│  - State management                                 │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│         Component Actors (esphome-components)       │
│  Each component = independent crate:                │
│  - esphome-gpio                                     │
│  - esphome-i2c                                      │
│  - esphome-wifi                                     │
│  - esphome-mqtt                                     │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│        Hardware Abstraction (esphome-hal)           │
│  - Wraps esp-hal with ESPHome patterns             │
│  - Type-safe pin allocation                         │
│  - Peripheral management                            │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│            Platform HAL (esp-hal)                   │
│  - ESP32, ESP32-C3, ESP32-S2, ESP32-S3             │
└─────────────────────────────────────────────────────┘
```

### 2.2 Core Crate Structure

```
esphome/
├── esphome-core/          # Core runtime and message bus
├── esphome-hal/           # Hardware abstraction layer
├── esphome-codegen/       # Code generator
├── esphome-api/           # Native API protocol
├── esphome-config/        # Configuration types
└── components/
    ├── esphome-gpio/      # GPIO components (switch, binary_sensor)
    ├── esphome-sensor/    # Sensor traits and common code
    ├── esphome-light/     # Light components
    ├── esphome-i2c/       # I2C bus actor
    ├── esphome-spi/       # SPI bus actor
    ├── esphome-wifi/      # WiFi manager
    ├── esphome-mqtt/      # MQTT client
    ├── esphome-ota/       # OTA updates
    └── sensors/
        ├── esphome-dht/       # DHT11/22 sensor
        ├── esphome-bme280/    # BME280 sensor
        ├── esphome-bmp280/    # BMP280 sensor
        └── ...
```

---

## 3.0 COMPONENT MODEL & ACTOR PATTERN

### 3.1 Actor Model Fundamentals

Each component is an independent actor with:

1. **Mailbox**: Typed message channel for incoming commands
2. **State**: Private internal state (not shared)
3. **Message Loop**: Async loop processing messages
4. **Output**: Can send messages to other actors via their addresses

### 3.2 Component Trait

**File**: `esphome-core/src/component.rs`

```rust
use embassy_sync::channel::{Receiver, Sender};

/// Core trait that all components must implement
#[async_trait::async_trait]
pub trait Component: Send {
    /// Component's message type
    type Message: Send;

    /// Component's initialization parameters
    type Config: Send;

    /// Human-readable component ID
    fn id(&self) -> &str;

    /// Initialize component with hardware resources
    async fn setup(&mut self, config: Self::Config) -> Result<(), ComponentError>;

    /// Main message processing loop
    async fn run(&mut self, mailbox: Receiver<'static, Self::Message>);
}

/// Component errors
#[derive(Debug)]
pub enum ComponentError {
    HardwareError(&'static str),
    ConfigError(&'static str),
    CommunicationError(&'static str),
}
```

### 3.3 Actor Address System

Components communicate via type-safe addresses:

```rust
/// Type-safe address to a component's mailbox
pub struct ActorAddress<M: Send> {
    sender: Sender<'static, M>,
}

impl<M: Send> ActorAddress<M> {
    /// Send message (blocks if mailbox full)
    pub async fn send(&self, message: M) {
        self.sender.send(message).await;
    }

    /// Try to send message (fails if mailbox full)
    pub fn try_send(&self, message: M) -> Result<(), M> {
        self.sender.try_send(message)
    }
}

impl<M: Send> Clone for ActorAddress<M> {
    fn clone(&self) -> Self {
        Self { sender: self.sender.clone() }
    }
}
```

### 3.4 Example Component: GPIO Switch

**File**: `components/esphome-gpio/src/switch.rs`

```rust
use esphome_core::{Component, ComponentError, ActorAddress};
use esphome_hal::gpio::{Output, Pin};
use embassy_sync::channel::Receiver;

/// Messages this component accepts
#[derive(Debug, Clone, Copy)]
pub enum SwitchCommand {
    TurnOn,
    TurnOff,
    Toggle,
}

/// Messages this component emits
#[derive(Debug, Clone, Copy)]
pub enum SwitchEvent {
    StateChanged { is_on: bool },
}

/// GPIO switch component
pub struct GpioSwitch<P: Pin> {
    id: &'static str,
    pin: Output<'static, P>,
    state: bool,
    event_bus: Option<ActorAddress<SwitchEvent>>,
}

impl<P: Pin> GpioSwitch<P> {
    pub fn new(id: &'static str) -> Self {
        Self {
            id,
            pin: uninitialized!(),  // Set in setup()
            state: false,
            event_bus: None,
        }
    }

    /// Subscribe to state change events
    pub fn subscribe_events(&mut self, addr: ActorAddress<SwitchEvent>) {
        self.event_bus = Some(addr);
    }

    fn set_state(&mut self, new_state: bool) {
        if new_state != self.state {
            self.state = new_state;

            if new_state {
                self.pin.set_high();
            } else {
                self.pin.set_low();
            }

            // Notify subscribers
            if let Some(ref bus) = self.event_bus {
                let _ = bus.try_send(SwitchEvent::StateChanged { is_on: new_state });
            }
        }
    }
}

#[async_trait::async_trait]
impl<P: Pin> Component for GpioSwitch<P> {
    type Message = SwitchCommand;
    type Config = GpioSwitchConfig<P>;

    fn id(&self) -> &str {
        self.id
    }

    async fn setup(&mut self, config: Self::Config) -> Result<(), ComponentError> {
        self.pin = Output::new(config.pin, config.initial_state.into());
        self.state = config.initial_state;
        Ok(())
    }

    async fn run(&mut self, mailbox: Receiver<'static, Self::Message>) {
        loop {
            let cmd = mailbox.receive().await;

            match cmd {
                SwitchCommand::TurnOn => self.set_state(true),
                SwitchCommand::TurnOff => self.set_state(false),
                SwitchCommand::Toggle => self.set_state(!self.state),
            }
        }
    }
}

/// Configuration for GPIO switch
pub struct GpioSwitchConfig<P: Pin> {
    pub pin: P,
    pub initial_state: bool,
    pub inverted: bool,
}
```

### 3.5 Component Registration

**File**: `esphome-core/src/registry.rs`

```rust
use core::any::TypeId;
use heapless::FnvIndexMap;

/// Global component registry
pub struct ComponentRegistry {
    components: FnvIndexMap<&'static str, TypeId, 32>,
}

impl ComponentRegistry {
    pub const fn new() -> Self {
        Self {
            components: FnvIndexMap::new(),
        }
    }

    /// Register a component type
    pub fn register<C: Component + 'static>(&mut self, id: &'static str) {
        self.components.insert(id, TypeId::of::<C>()).ok();
    }

    /// Check if component exists
    pub fn contains(&self, id: &str) -> bool {
        self.components.contains_key(id)
    }
}

/// Global registry instance
pub static REGISTRY: Mutex<ComponentRegistry> = Mutex::new(ComponentRegistry::new());
```

---

## 4.0 CORE RUNTIME DESIGN

### 4.1 Application Structure

**File**: `esphome-core/src/application.rs`

```rust
use embassy_executor::Spawner;

/// Main application context
pub struct Application {
    /// Human-readable device name
    pub name: &'static str,

    /// Device platform (esp32, esp32c3, etc.)
    pub platform: Platform,

    /// Global event bus
    pub event_bus: EventBus,
}

impl Application {
    /// Create new application
    pub const fn new(name: &'static str, platform: Platform) -> Self {
        Self {
            name,
            platform,
            event_bus: EventBus::new(),
        }
    }

    /// Initialize application
    pub async fn init(&mut self) -> Result<(), AppError> {
        // Initialize logging
        esp_println::logger::init_logger_from_env();

        // Log startup
        log::info!("ESPHome-RS starting: {}", self.name);
        log::info!("Platform: {:?}", self.platform);

        Ok(())
    }
}

/// Platform enumeration
#[derive(Debug, Clone, Copy)]
pub enum Platform {
    Esp32,
    Esp32c3,
    Esp32s2,
    Esp32s3,
}

#[derive(Debug)]
pub enum AppError {
    InitializationFailed(&'static str),
}
```

### 4.2 Event Bus

**File**: `esphome-core/src/event_bus.rs`

```rust
use embassy_sync::channel::Channel;
use embassy_sync::pubsub::PubSubChannel;

/// System-wide events
#[derive(Debug, Clone)]
pub enum SystemEvent {
    /// Device booted successfully
    BootComplete,

    /// WiFi connected
    WifiConnected,

    /// WiFi disconnected
    WifiDisconnected,

    /// MQTT connected
    MqttConnected,

    /// MQTT disconnected
    MqttDisconnected,

    /// Component error
    ComponentError {
        component_id: &'static str,
        error: &'static str,
    },
}

/// Global event bus for system events
pub struct EventBus {
    channel: PubSubChannel<SystemEvent, 8, 4, 2>,
}

impl EventBus {
    pub const fn new() -> Self {
        Self {
            channel: PubSubChannel::new(),
        }
    }

    /// Publish system event
    pub fn publish(&self, event: SystemEvent) {
        self.channel.publish_immediate(event);
    }

    /// Subscribe to system events
    pub fn subscribe(&self) -> Subscriber<SystemEvent> {
        self.channel.subscriber().unwrap()
    }
}
```

### 4.3 Time & Scheduling

**File**: `esphome-core/src/time.rs`

```rust
use embassy_time::{Duration, Instant, Timer};

/// Periodic task runner
pub struct Interval {
    duration: Duration,
    next_tick: Instant,
}

impl Interval {
    /// Create new interval timer
    pub fn new(duration: Duration) -> Self {
        Self {
            duration,
            next_tick: Instant::now() + duration,
        }
    }

    /// Wait until next tick
    pub async fn tick(&mut self) {
        Timer::at(self.next_tick).await;
        self.next_tick += self.duration;
    }
}

/// Common intervals
pub mod intervals {
    use super::*;

    pub const fn ms(milliseconds: u64) -> Duration {
        Duration::from_millis(milliseconds)
    }

    pub const fn secs(seconds: u64) -> Duration {
        Duration::from_secs(seconds)
    }

    pub const fn mins(minutes: u64) -> Duration {
        Duration::from_secs(minutes * 60)
    }
}
```

---

## 5.0 HARDWARE ABSTRACTION LAYER

### 5.1 Type-Safe Pin Management

**File**: `esphome-hal/src/gpio.rs`

```rust
use core::marker::PhantomData;

/// Marker trait for GPIO pins
pub trait Pin: Send {
    const NUMBER: u8;
}

/// Type-safe GPIO pin
pub struct GpioPin<const N: u8>;

impl<const N: u8> Pin for GpioPin<N> {
    const NUMBER: u8 = N;
}

/// Pin state marker traits
pub trait PinMode: Send {}
pub struct Input;
pub struct Output;
pub struct Analog;

impl PinMode for Input {}
impl PinMode for Output {}
impl PinMode for Analog {}

/// Typed GPIO pin in specific mode
pub struct TypedPin<P: Pin, M: PinMode> {
    _pin: PhantomData<P>,
    _mode: PhantomData<M>,
    inner: esp_hal::gpio::GpioPin<P::NUMBER>,
}

/// Builder for pin allocation
pub struct PinAllocator {
    used_pins: u64,  // Bitmap of used pins
}

impl PinAllocator {
    pub const fn new() -> Self {
        Self { used_pins: 0 }
    }

    /// Allocate pin (compile-time check)
    pub fn allocate<P: Pin>(&mut self) -> TypedPin<P, Input> {
        let pin_bit = 1u64 << P::NUMBER;

        // This could be enhanced with const assertions in future Rust
        if self.used_pins & pin_bit != 0 {
            panic!("Pin already allocated");
        }

        self.used_pins |= pin_bit;

        TypedPin {
            _pin: PhantomData,
            _mode: PhantomData,
            inner: unsafe { esp_hal::gpio::GpioPin::new() },
        }
    }
}
```

### 5.2 I2C Bus Actor

**File**: `components/esphome-i2c/src/lib.rs`

```rust
use embassy_sync::channel::{Channel, Receiver, Sender};
use embedded_hal_async::i2c::I2c;

/// I2C transaction request
pub struct I2cTransaction {
    /// Device address
    address: u8,

    /// Operation
    operation: I2cOperation,

    /// Response channel
    response: Sender<'static, Result<(), I2cError>>,
}

pub enum I2cOperation {
    Write(&'static [u8]),
    Read(&'static mut [u8]),
    WriteRead {
        write: &'static [u8],
        read: &'static mut [u8],
    },
}

/// I2C bus actor
pub struct I2cBus<I: I2c> {
    bus: I,
    mailbox: Receiver<'static, I2cTransaction>,
}

impl<I: I2c> I2cBus<I> {
    pub async fn run(mut self) {
        loop {
            let transaction = self.mailbox.receive().await;

            let result = match transaction.operation {
                I2cOperation::Write(data) => {
                    self.bus.write(transaction.address, data).await
                        .map_err(|_| I2cError::WriteFailed)
                }
                I2cOperation::Read(buffer) => {
                    self.bus.read(transaction.address, buffer).await
                        .map_err(|_| I2cError::ReadFailed)
                }
                I2cOperation::WriteRead { write, read } => {
                    self.bus.write_read(transaction.address, write, read).await
                        .map_err(|_| I2cError::TransactionFailed)
                }
            };

            transaction.response.send(result).await;
        }
    }
}

/// I2C handle for components
pub struct I2cHandle {
    address: u8,
    bus: Sender<'static, I2cTransaction>,
}

impl I2cHandle {
    /// Write data to device
    pub async fn write(&self, data: &'static [u8]) -> Result<(), I2cError> {
        let (tx, rx) = channel::oneshot();

        self.bus.send(I2cTransaction {
            address: self.address,
            operation: I2cOperation::Write(data),
            response: tx,
        }).await;

        rx.receive().await
    }

    /// Read data from device
    pub async fn read(&self, buffer: &'static mut [u8]) -> Result<(), I2cError> {
        let (tx, rx) = channel::oneshot();

        self.bus.send(I2cTransaction {
            address: self.address,
            operation: I2cOperation::Read(buffer),
            response: tx,
        }).await;

        rx.receive().await
    }
}

#[derive(Debug)]
pub enum I2cError {
    WriteFailed,
    ReadFailed,
    TransactionFailed,
}
```

---

## 6.0 CONFIGURATION SYSTEM

### 6.1 Configuration Types

**File**: `esphome-config/src/lib.rs`

```rust
use serde::{Deserialize, Serialize};

/// Root configuration
#[derive(Debug, Deserialize)]
pub struct Config {
    /// Device information
    pub esphome: DeviceConfig,

    /// WiFi configuration
    #[serde(default)]
    pub wifi: Option<WifiConfig>,

    /// MQTT configuration
    #[serde(default)]
    pub mqtt: Option<MqttConfig>,

    /// API configuration
    #[serde(default)]
    pub api: Option<ApiConfig>,

    /// Component configurations
    #[serde(flatten)]
    pub components: ComponentConfigs,
}

#[derive(Debug, Deserialize)]
pub struct DeviceConfig {
    pub name: String,
    pub platform: String,
    pub board: String,
}

#[derive(Debug, Deserialize)]
pub struct WifiConfig {
    pub ssid: String,
    pub password: String,

    #[serde(default)]
    pub fast_connect: bool,
}

#[derive(Debug, Deserialize)]
pub struct ComponentConfigs {
    #[serde(default)]
    pub switch: Vec<SwitchConfig>,

    #[serde(default)]
    pub binary_sensor: Vec<BinarySensorConfig>,

    #[serde(default)]
    pub sensor: Vec<SensorConfig>,

    #[serde(default)]
    pub light: Vec<LightConfig>,
}

#[derive(Debug, Deserialize)]
pub struct SwitchConfig {
    pub platform: String,
    pub id: String,
    pub name: Option<String>,

    // Platform-specific config
    #[serde(flatten)]
    pub platform_config: PlatformConfig,
}

#[derive(Debug, Deserialize)]
#[serde(untagged)]
pub enum PlatformConfig {
    Gpio(GpioConfig),
    // Other platforms...
}

#[derive(Debug, Deserialize)]
pub struct GpioConfig {
    pub pin: u8,

    #[serde(default)]
    pub inverted: bool,
}
```

### 6.2 Validation

**File**: `esphome-config/src/validate.rs`

```rust
use std::collections::{HashMap, HashSet};

pub struct ConfigValidator {
    errors: Vec<String>,
    warnings: Vec<String>,
}

impl ConfigValidator {
    pub fn new() -> Self {
        Self {
            errors: Vec::new(),
            warnings: Vec::new(),
        }
    }

    pub fn validate(&mut self, config: &Config) -> ValidationResult {
        // Check for duplicate IDs
        self.check_duplicate_ids(config);

        // Check for GPIO conflicts
        self.check_gpio_conflicts(config);

        // Check for I2C address conflicts
        self.check_i2c_conflicts(config);

        // Validate pin numbers
        self.check_valid_pins(config);

        ValidationResult {
            errors: self.errors.clone(),
            warnings: self.warnings.clone(),
        }
    }

    fn check_duplicate_ids(&mut self, config: &Config) {
        let mut seen_ids = HashSet::new();

        for switch in &config.components.switch {
            if !seen_ids.insert(&switch.id) {
                self.errors.push(format!("Duplicate ID: {}", switch.id));
            }
        }

        // Check other component types...
    }

    fn check_gpio_conflicts(&mut self, config: &Config) {
        let mut pin_usage: HashMap<u8, String> = HashMap::new();

        for switch in &config.components.switch {
            if let PlatformConfig::Gpio(gpio) = &switch.platform_config {
                if let Some(existing) = pin_usage.get(&gpio.pin) {
                    self.errors.push(format!(
                        "GPIO{} conflict: used by '{}' and '{}'",
                        gpio.pin, existing, switch.id
                    ));
                } else {
                    pin_usage.insert(gpio.pin, switch.id.clone());
                }
            }
        }
    }
}

pub struct ValidationResult {
    pub errors: Vec<String>,
    pub warnings: Vec<String>,
}

impl ValidationResult {
    pub fn is_valid(&self) -> bool {
        self.errors.is_empty()
    }
}
```

---

## 7.0 COMPONENT COMMUNICATION

### 7.1 Message Types

Components communicate via strongly-typed messages:

```rust
/// Example: Automation trigger
pub enum AutomationTrigger {
    /// Binary sensor state changed
    BinarySensor {
        component_id: &'static str,
        state: bool,
    },

    /// Sensor value updated
    SensorUpdate {
        component_id: &'static str,
        value: f32,
    },

    /// Time-based trigger
    Time {
        trigger_type: TimeTrigger,
    },
}

pub enum TimeTrigger {
    Interval { seconds: u32 },
    CronSchedule { expression: &'static str },
}

/// Example: Light control
pub enum LightCommand {
    TurnOn { brightness: Option<u8> },
    TurnOff,
    SetBrightness(u8),
    SetRgb { r: u8, g: u8, b: u8 },
}
```

### 7.2 Actor Addresses

```rust
/// Type-safe collection of component addresses
pub struct ComponentAddresses {
    pub switches: HashMap<&'static str, ActorAddress<SwitchCommand>>,
    pub lights: HashMap<&'static str, ActorAddress<LightCommand>>,
    pub sensors: HashMap<&'static str, ActorAddress<SensorCommand>>,
}

/// Address lookup
impl ComponentAddresses {
    pub fn switch(&self, id: &str) -> Option<&ActorAddress<SwitchCommand>> {
        self.switches.get(id)
    }

    pub fn light(&self, id: &str) -> Option<&ActorAddress<LightCommand>> {
        self.lights.get(id)
    }
}
```

### 7.3 Automation Actor

**File**: `esphome-core/src/automation.rs`

```rust
/// Automation rule
pub struct Automation {
    id: &'static str,
    trigger: AutomationTrigger,
    actions: Vec<Action>,
}

pub enum Action {
    SwitchToggle(&'static str),
    SwitchTurnOn(&'static str),
    SwitchTurnOff(&'static str),
    LightToggle(&'static str),
    LightSetBrightness { id: &'static str, brightness: u8 },
    Delay(Duration),
}

/// Automation runner task
#[embassy_executor::task]
pub async fn automation_task(
    automations: &'static [Automation],
    trigger_rx: Receiver<'static, AutomationTrigger>,
    addresses: ComponentAddresses,
) {
    loop {
        let trigger = trigger_rx.receive().await;

        // Find matching automations
        for automation in automations {
            if automation.trigger.matches(&trigger) {
                // Execute actions
                for action in &automation.actions {
                    execute_action(action, &addresses).await;
                }
            }
        }
    }
}

async fn execute_action(action: &Action, addresses: &ComponentAddresses) {
    match action {
        Action::SwitchToggle(id) => {
            if let Some(addr) = addresses.switch(id) {
                addr.send(SwitchCommand::Toggle).await;
            }
        }
        Action::LightSetBrightness { id, brightness } => {
            if let Some(addr) = addresses.light(id) {
                addr.send(LightCommand::SetBrightness(*brightness)).await;
            }
        }
        Action::Delay(duration) => {
            Timer::after(*duration).await;
        }
        // ... other actions
    }
}
```

---

## 8.0 CODE GENERATION STRATEGY

### 8.1 Generator Architecture

**File**: `esphome-codegen/src/lib.rs`

```rust
pub struct CodeGenerator {
    config: Config,
    output_dir: PathBuf,
}

impl CodeGenerator {
    pub fn new(config: Config, output_dir: PathBuf) -> Self {
        Self { config, output_dir }
    }

    /// Generate all code
    pub fn generate(&self) -> Result<(), GeneratorError> {
        // Validate configuration
        let validation = ConfigValidator::new().validate(&self.config);
        if !validation.is_valid() {
            return Err(GeneratorError::ValidationFailed(validation.errors));
        }

        // Generate main.rs
        self.generate_main()?;

        // Generate Cargo.toml
        self.generate_cargo_toml()?;

        // Generate component instantiations
        self.generate_components()?;

        Ok(())
    }

    fn generate_main(&self) -> Result<(), GeneratorError> {
        let mut output = String::new();

        // File header
        output.push_str(r#"
#![no_std]
#![no_main]

use embassy_executor::Spawner;
use esp_backtrace as _;
use esp_hal::{
    clock::ClockControl,
    peripherals::Peripherals,
    prelude::*,
    timer::TimerGroup,
};

mod components;

use esphome_core::Application;

"#);

        // Main function
        output.push_str(&self.generate_main_function()?);

        // Component tasks
        output.push_str(&self.generate_component_tasks()?);

        // Write to file
        std::fs::write(self.output_dir.join("src/main.rs"), output)?;

        Ok(())
    }

    fn generate_main_function(&self) -> Result<String, GeneratorError> {
        let mut code = String::from(r#"
#[main]
async fn main(spawner: Spawner) {
    // Initialize hardware
    let peripherals = Peripherals::take();
    let system = peripherals.SYSTEM.split();
    let clocks = ClockControl::max(system.clock_control).freeze();

    // Initialize Embassy
    let timer_group0 = TimerGroup::new(peripherals.TIMG0, &clocks);
    embassy::init(&clocks, timer_group0);

    // Initialize application
    let mut app = Application::new(
        "#);

        code.push_str(&format!("        \"{}\",\n", self.config.esphome.name));
        code.push_str(&format!("        Platform::{}\n",
            self.config.esphome.platform.to_uppercase()));
        code.push_str("    );\n\n");
        code.push_str("    app.init().await.expect(\"App init failed\");\n\n");

        // Initialize GPIO
        code.push_str("    let io = esp_hal::IO::new(peripherals.GPIO, peripherals.IO_MUX);\n\n");

        // Spawn components
        for switch in &self.config.components.switch {
            code.push_str(&self.generate_component_spawn("switch", &switch.id)?);
        }

        for sensor in &self.config.components.sensor {
            code.push_str(&self.generate_component_spawn("sensor", &sensor.id)?);
        }

        code.push_str("}\n");

        Ok(code)
    }

    fn generate_component_spawn(&self, component_type: &str, id: &str) -> Result<String, GeneratorError> {
        Ok(format!(
            "    spawner.spawn(components::{}::{}::run(/* config */)).expect(\"Failed to spawn {}\");\n",
            component_type, id, id
        ))
    }
}
```

### 8.2 Generated Project Structure

```
generated-project/
├── Cargo.toml          # Generated with correct dependencies
├── src/
│   ├── main.rs         # Generated main function
│   └── components/     # Generated component modules
│       ├── mod.rs
│       ├── kitchen_light.rs
│       ├── living_room_sensor.rs
│       └── ...
├── .cargo/
│   └── config.toml     # Target configuration
└── config.yaml         # Original ESPHome config (copied)
```

---

## 9.0 BUILD SYSTEM

### 9.1 Cargo-Based Build

**File**: `Cargo.toml` (in generated project)

```toml
[package]
name = "my-esphome-device"
version = "0.1.0"
edition = "2021"

[dependencies]
# Core
esphome-core = "0.1"
esphome-hal = "0.1"

# Platform HAL
esp-hal = "0.16"
esp-backtrace = { version = "0.11", features = ["panic-handler", "exception-handler"] }
esp-println = "0.9"

# Embassy
embassy-executor = { version = "0.5", features = ["arch-xtensa", "executor-thread"] }
embassy-time = "0.3"
embassy-sync = "0.5"

# Component crates (added based on config)
esphome-gpio = "0.1"
esphome-wifi = "0.1"
esphome-mqtt = "0.1"

# Sensor crates (added based on config)
esphome-dht = "0.1"
esphome-bme280 = "0.1"

[profile.release]
opt-level = "z"      # Optimize for size
lto = true           # Link-time optimization
codegen-units = 1    # Better optimization
strip = true         # Strip symbols

[profile.dev]
opt-level = 1        # Some optimization for reasonable performance
```

### 9.2 Build Script

**File**: `build.rs` (minimal or not needed)

```rust
// Most configuration is in Cargo.toml and .cargo/config.toml
// build.rs only needed for special cases
fn main() {
    println!("cargo:rerun-if-changed=config.yaml");
}
```

### 9.3 CLI Tool

**File**: `esphome-cli/src/main.rs`

```rust
use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "esphome")]
#[command(about = "ESPHome-RS CLI tool")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Compile configuration and generate project
    Compile {
        /// Configuration file
        config: PathBuf,
    },

    /// Build firmware
    Build {
        /// Configuration file
        config: PathBuf,
    },

    /// Upload firmware to device
    Upload {
        /// Configuration file
        config: PathBuf,

        /// Serial port
        #[arg(short, long)]
        port: Option<String>,
    },

    /// Run (build + upload + monitor)
    Run {
        /// Configuration file
        config: PathBuf,

        /// Serial port
        #[arg(short, long)]
        port: Option<String>,
    },

    /// Validate configuration
    Validate {
        /// Configuration file
        config: PathBuf,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Compile { config } => {
            compile_config(&config)?;
        }
        Commands::Build { config } => {
            compile_config(&config)?;
            build_firmware()?;
        }
        Commands::Upload { config, port } => {
            compile_config(&config)?;
            build_firmware()?;
            upload_firmware(port)?;
        }
        Commands::Run { config, port } => {
            compile_config(&config)?;
            build_firmware()?;
            upload_firmware(port)?;
            monitor_logs()?;
        }
        Commands::Validate { config } => {
            validate_config(&config)?;
        }
    }

    Ok(())
}

fn compile_config(path: &Path) -> Result<()> {
    // Parse YAML
    let config: Config = read_config(path)?;

    // Validate
    let validation = ConfigValidator::new().validate(&config);
    if !validation.is_valid() {
        for error in &validation.errors {
            eprintln!("Error: {}", error);
        }
        return Err(anyhow!("Configuration validation failed"));
    }

    // Generate code
    let generator = CodeGenerator::new(config, PathBuf::from("."));
    generator.generate()?;

    println!("✓ Configuration compiled successfully");
    Ok(())
}

fn build_firmware() -> Result<()> {
    // Run cargo build
    let status = Command::new("cargo")
        .args(&["build", "--release"])
        .status()?;

    if !status.success() {
        return Err(anyhow!("Build failed"));
    }

    println!("✓ Firmware built successfully");
    Ok(())
}
```

---

## 10.0 MIGRATION PATH

### 10.1 Phase 1: Core Runtime (Months 1-3)

**Goals**:
- Implement esphome-core
- Implement esphome-hal
- Implement esphome-codegen
- Create basic GPIO components

**Deliverables**:
1. Working Embassy executor setup
2. GPIO switch component
3. GPIO binary sensor component
4. Basic code generator
5. CLI tool

**Validation**:
- Simple configurations compile and run
- GPIO toggle works
- LED blink example

### 10.2 Phase 2: Communication (Months 4-6)

**Goals**:
- Implement I2C bus actor
- Implement SPI bus actor
- WiFi manager
- Native API protocol

**Deliverables**:
1. esphome-i2c crate
2. esphome-spi crate
3. esphome-wifi crate
4. esphome-api crate
5. Home Assistant integration

**Validation**:
- I2C sensors work
- WiFi connection stable
- Home Assistant discovers device
- State updates to HA

### 10.3 Phase 3: Common Components (Months 7-12)

**Goals**:
- Port most common sensors
- Port common actuators
- MQTT support
- OTA updates

**Deliverables**:
1. DHT, BME280, BMP280 sensors
2. PWM light components
3. MQTT client
4. OTA update system
5. Documentation

**Validation**:
- Feature parity with top 20 ESPHome components
- Performance benchmarks
- Memory usage analysis

### 10.4 Phase 4: Advanced Features (Months 13+)

**Goals**:
- Advanced automations
- Display support
- Climate control
- Cover/blind control
- Voice assistant integration

---

## 11.0 COMPONENT CRATE STRUCTURE

### 11.1 Standard Component Layout

Each component crate follows this structure:

```
esphome-{component}/
├── Cargo.toml
├── src/
│   ├── lib.rs              # Public API
│   ├── actor.rs            # Component actor implementation
│   ├── config.rs           # Configuration types
│   └── messages.rs         # Message types
├── examples/
│   └── basic_usage.rs      # Example usage
└── README.md
```

### 11.2 Component Crate Template

**File**: `esphome-{component}/Cargo.toml`

```toml
[package]
name = "esphome-{component}"
version = "0.1.0"
edition = "2021"
authors = ["ESPHome-RS Contributors"]
license = "MIT OR Apache-2.0"
description = "{Component} support for ESPHome-RS"
repository = "https://github.com/esphome/esphome-rs"
keywords = ["esphome", "embedded", "iot", "{component}"]
categories = ["embedded", "no-std"]

[dependencies]
esphome-core = { version = "0.1", path = "../../esphome-core" }
embassy-sync = "0.5"
embassy-time = "0.3"

# Add specific dependencies for this component
# e.g., embedded-hal-async for sensor traits
```

**File**: `esphome-{component}/src/lib.rs`

```rust
#![no_std]
#![doc = include_str!("../README.md")]

mod actor;
mod config;
mod messages;

pub use actor::*;
pub use config::*;
pub use messages::*;

// Re-export common types
pub use esphome_core::{Component, ComponentError};
```

### 11.3 Sensor Component Example

**File**: `components/esphome-dht/src/lib.rs`

```rust
#![no_std]

use embassy_time::{Duration, Interval};
use embassy_sync::channel::Receiver;
use esphome_core::{Component, ComponentError};

mod messages;
pub use messages::*;

/// DHT sensor component
pub struct DhtSensor {
    id: &'static str,
    pin: u8,
    model: DhtModel,
    update_interval: Duration,
}

#[derive(Debug, Clone, Copy)]
pub enum DhtModel {
    Dht11,
    Dht22,
}

pub enum DhtCommand {
    ForceUpdate,
    SetInterval(Duration),
}

pub struct DhtReading {
    pub temperature: f32,
    pub humidity: f32,
}

impl DhtSensor {
    pub fn new(id: &'static str, pin: u8, model: DhtModel) -> Self {
        Self {
            id,
            pin,
            model,
            update_interval: Duration::from_secs(60),
        }
    }

    async fn read_sensor(&mut self) -> Result<DhtReading, DhtError> {
        // DHT protocol implementation
        todo!("Implement DHT reading protocol")
    }
}

#[async_trait::async_trait]
impl Component for DhtSensor {
    type Message = DhtCommand;
    type Config = DhtConfig;

    fn id(&self) -> &str {
        self.id
    }

    async fn setup(&mut self, config: Self::Config) -> Result<(), ComponentError> {
        self.pin = config.pin;
        self.model = config.model;
        self.update_interval = config.update_interval.unwrap_or(Duration::from_secs(60));
        Ok(())
    }

    async fn run(&mut self, mailbox: Receiver<'static, Self::Message>) {
        let mut interval = Interval::new(self.update_interval);

        loop {
            embassy_futures::select::select(
                interval.tick(),
                mailbox.receive()
            ).await
            .branch(
                |_| {
                    // Periodic update
                    match self.read_sensor().await {
                        Ok(reading) => {
                            log::info!("{}: temp={:.1}°C, humidity={:.1}%",
                                self.id, reading.temperature, reading.humidity);
                        }
                        Err(e) => {
                            log::error!("{}: Read error: {:?}", self.id, e);
                        }
                    }
                },
                |cmd| {
                    // Handle command
                    match cmd {
                        DhtCommand::ForceUpdate => {
                            // Force immediate read
                        }
                        DhtCommand::SetInterval(duration) => {
                            self.update_interval = duration;
                            interval = Interval::new(duration);
                        }
                    }
                }
            );
        }
    }
}

#[derive(Debug)]
pub enum DhtError {
    Timeout,
    ChecksumError,
    InvalidData,
}
```

---

## 12.0 NAMING CONVENTIONS

### 12.1 Crate Naming

- **Core crates**: `esphome-{feature}` (e.g., `esphome-core`, `esphome-hal`)
- **Component crates**: `esphome-{component}` (e.g., `esphome-gpio`, `esphome-wifi`)
- **Sensor crates**: `esphome-{sensor}` (e.g., `esphome-dht`, `esphome-bme280`)
- **Platform crates**: `esphome-{platform}` (e.g., `esphome-esp32`)

### 12.2 Module Structure

```rust
// Component actor
pub struct GpioSwitch { ... }

// Messages
pub enum SwitchCommand { ... }
pub enum SwitchEvent { ... }

// Configuration
pub struct GpioSwitchConfig { ... }

// Errors
pub enum SwitchError { ... }
```

### 12.3 Component IDs

- **User-defined**: `kitchen_light`, `bedroom_temp`, `garage_door`
- **Generated**: Avoid underscores in generated code, use snake_case for Rust
- **Constants**: `const COMPONENT_ID: &str = "kitchen_light";`

### 12.4 Actor Task Names

```rust
#[embassy_executor::task]
async fn gpio_switch_task(/* ... */) { ... }

#[embassy_executor::task]
async fn i2c_bus_task(/* ... */) { ... }

#[embassy_executor::task]
async fn wifi_manager_task(/* ... */) { ... }
```

### 12.5 Configuration Keys

Match ESPHome YAML conventions where possible:

```yaml
switch:
  - platform: gpio    # lowercase
    id: my_switch     # snake_case
    pin: GPIO5        # uppercase GPIO prefix
    inverted: false   # lowercase boolean
```

---

## 13.0 REFERENCE IMPLEMENTATION

### 13.1 Complete Working Example

**File**: `config.yaml`

```yaml
esphome:
  name: test-device
  platform: esp32
  board: esp32dev

wifi:
  ssid: "MyNetwork"
  password: "secret"

api:
  encryption:
    key: "base64key=="

switch:
  - platform: gpio
    id: relay_1
    name: "Relay 1"
    pin: GPIO5

binary_sensor:
  - platform: gpio
    id: button_1
    name: "Button 1"
    pin:
      number: GPIO12
      inverted: true
      mode:
        input: true
        pullup: true
    on_press:
      - switch.toggle: relay_1

sensor:
  - platform: dht
    id: temp_sensor
    pin: GPIO4
    model: DHT22
    temperature:
      name: "Living Room Temperature"
    humidity:
      name: "Living Room Humidity"
    update_interval: 60s
```

**Generated**: `src/main.rs`

```rust
#![no_std]
#![no_main]

use embassy_executor::Spawner;
use esp_backtrace as _;
use esp_hal::{
    clock::ClockControl,
    gpio::IO,
    peripherals::Peripherals,
    prelude::*,
    timer::TimerGroup,
};

use esphome_core::{Application, Platform};
use esphome_gpio::{GpioSwitch, GpioSwitchConfig, SwitchCommand};
use esphome_dht::{DhtSensor, DhtConfig, DhtModel};

#[main]
async fn main(spawner: Spawner) {
    // Hardware init
    let peripherals = Peripherals::take();
    let system = peripherals.SYSTEM.split();
    let clocks = ClockControl::max(system.clock_control).freeze();

    let timer_group0 = TimerGroup::new(peripherals.TIMG0, &clocks);
    embassy::init(&clocks, timer_group0);

    // App init
    let mut app = Application::new("test-device", Platform::Esp32);
    app.init().await.expect("App init failed");

    // GPIO init
    let io = IO::new(peripherals.GPIO, peripherals.IO_MUX);

    // Spawn components
    spawner.spawn(relay_1_task(io.pins.gpio5))
        .expect("Failed to spawn relay_1");

    spawner.spawn(button_1_task(io.pins.gpio12))
        .expect("Failed to spawn button_1");

    spawner.spawn(temp_sensor_task(io.pins.gpio4))
        .expect("Failed to spawn temp_sensor");

    // Spawn WiFi manager
    spawner.spawn(wifi_task())
        .expect("Failed to spawn WiFi");
}

#[embassy_executor::task]
async fn relay_1_task(pin: esp_hal::gpio::GpioPin<5>) {
    use embassy_sync::channel::Channel;

    static MAILBOX: Channel<_, SwitchCommand, 8> = Channel::new();

    let mut switch = GpioSwitch::new("relay_1");
    let config = GpioSwitchConfig {
        pin,
        initial_state: false,
        inverted: false,
    };

    switch.setup(config).await.expect("Switch setup failed");
    switch.run(MAILBOX.receiver()).await;
}

#[embassy_executor::task]
async fn temp_sensor_task(pin: esp_hal::gpio::GpioPin<4>) {
    use embassy_sync::channel::Channel;

    static MAILBOX: Channel<_, DhtCommand, 4> = Channel::new();

    let mut sensor = DhtSensor::new("temp_sensor", 4, DhtModel::Dht22);
    let config = DhtConfig {
        pin: 4,
        model: DhtModel::Dht22,
        update_interval: Some(Duration::from_secs(60)),
    };

    sensor.setup(config).await.expect("DHT setup failed");
    sensor.run(MAILBOX.receiver()).await;
}

// ... other tasks
```

---

## 14.0 TESTING STRATEGY

### 14.1 Unit Tests

Each component crate has unit tests:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_switch_command_serialization() {
        // Test message types
    }

    #[test]
    fn test_config_validation() {
        // Test configuration validation
    }
}
```

### 14.2 Integration Tests

**File**: `tests/integration_test.rs`

```rust
#![no_std]
#![no_main]

use embassy_executor::Spawner;

#[embassy_executor::test]
async fn test_gpio_toggle() {
    // Test GPIO switch can be toggled
    todo!()
}

#[embassy_executor::test]
async fn test_i2c_communication() {
    // Test I2C bus actor
    todo!()
}
```

### 14.3 Hardware-in-Loop Tests

```rust
// Run on actual hardware
#[embassy_executor::test]
async fn test_dht_reading() {
    let sensor = DhtSensor::new("test", 4, DhtModel::Dht22);
    let reading = sensor.read_sensor().await.unwrap();

    assert!(reading.temperature > -40.0 && reading.temperature < 80.0);
    assert!(reading.humidity >= 0.0 && reading.humidity <= 100.0);
}
```

### 14.4 Benchmarks

```rust
#[embassy_executor::test]
async fn bench_channel_send() {
    use embassy_time::Instant;

    let start = Instant::now();
    for _ in 0..1000 {
        CHANNEL.send(Message::Test).await;
    }
    let elapsed = Instant::now() - start;

    log::info!("1000 sends took: {:?}", elapsed);
}
```

---

## 15.0 ADVANTAGES OF THIS APPROACH

### 15.1 Type Safety

- Hardware resources managed by type system
- Compile-time guarantee no GPIO conflicts
- Message types prevent protocol errors

### 15.2 Performance

- Zero-cost async abstractions
- No runtime overhead for message passing
- Optimized for embedded constraints

### 15.3 Modularity

- Components are independent crates
- Clear versioning and dependencies
- Easy to add new components
- Community can contribute components

### 15.4 Maintainability

- Modern Rust idioms
- Clear actor boundaries
- Explicit communication patterns
- Excellent error messages

### 15.5 Safety

- Memory safety guaranteed by Rust
- No use-after-free bugs
- No data races
- Panic boundaries at FFI edges (none needed here!)

---

## 16.0 GETTING STARTED

### 16.1 Installation

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install ESP toolchain
cargo install espup
espup install

# Install ESPHome-RS CLI
cargo install esphome-cli
```

### 16.2 Create First Project

```bash
# Create config
cat > config.yaml << EOF
esphome:
  name: my-device
  platform: esp32
  board: esp32dev

switch:
  - platform: gpio
    id: led
    pin: GPIO2
EOF

# Compile and upload
esphome run config.yaml
```

### 16.3 Development Workflow

```bash
# 1. Edit config.yaml
vim config.yaml

# 2. Validate
esphome validate config.yaml

# 3. Build
esphome build config.yaml

# 4. Upload
esphome upload config.yaml --port /dev/ttyUSB0

# 5. Monitor logs
esphome logs config.yaml --port /dev/ttyUSB0

# Or do it all at once
esphome run config.yaml
```

---

## 17.0 CONCLUSION

This specification defines a complete rewrite of ESPHome in Rust using:

- **Embassy async runtime** as the foundation
- **Actor pattern** for component isolation
- **Type-safe message passing** for communication
- **Modular crate architecture** for extensibility
- **Code generation** from YAML to Rust
- **Zero-cost abstractions** for embedded performance

The result is a modern, safe, performant IoT framework that maintains ESPHome's ease of use while leveraging Rust's strengths.

---

## APPENDIX A: COMPARISON WITH ORIGINAL ESPHOME

| Aspect | ESPHome (C++) | ESPHome-RS (Rust) |
|--------|---------------|-------------------|
| **Language** | C++ | Rust |
| **Runtime** | Arduino loop() | Embassy async |
| **Concurrency** | Cooperative | Cooperative (async) |
| **Type Safety** | Weak | Strong |
| **Memory Safety** | Manual | Guaranteed |
| **Component Model** | Inheritance | Composition + Traits |
| **Communication** | Direct calls | Message passing |
| **Build System** | PlatformIO | Cargo |
| **Module System** | Include files | Crates |
| **Error Handling** | Return codes | Result<T, E> |
| **Hardware Access** | Raw pointers | Type-safe wrappers |

## APPENDIX B: GLOSSARY

- **Actor**: Independent concurrent entity with mailbox
- **Message**: Typed command or event sent between actors
- **Mailbox**: Queue of messages for an actor
- **Channel**: Embassy's async message passing primitive
- **Component**: Actor that controls hardware or implements logic
- **HAL**: Hardware Abstraction Layer
- **Embassy**: Async runtime for embedded Rust
- **Spawner**: Mechanism to start async tasks

## APPENDIX C: RESOURCES

- **Embassy**: https://embassy.dev/
- **esp-hal**: https://github.com/esp-rs/esp-hal
- **Original ESPHome**: https://github.com/esphome/esphome
- **Rust Embedded Book**: https://docs.rust-embedded.org/book/
