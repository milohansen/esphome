#![no_std]
extern crate alloc;
use alloc::string::String;
use alloc::vec::Vec;
use serde::{Deserialize, Serialize};

/// Root configuration
#[derive(Debug, Deserialize, Serialize)]
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

#[derive(Debug, Deserialize, Serialize)]
pub struct DeviceConfig {
    pub name: String,
    pub platform: String,
    pub board: String,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct WifiConfig {
    pub ssid: String,
    pub password: String,

    #[serde(default)]
    pub fast_connect: bool,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct MqttConfig {
    pub broker: String,
    #[serde(default)]
    pub port: u16,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct ApiConfig {
    #[serde(default)]
    pub port: u16,
}

#[derive(Debug, Deserialize, Serialize)]
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

#[derive(Debug, Deserialize, Serialize)]
pub struct SwitchConfig {
    pub platform: String,
    pub id: String,
    pub name: Option<String>,

    // Platform-specific config
    #[serde(flatten)]
    pub platform_config: PlatformConfig,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct BinarySensorConfig {
    pub platform: String,
    pub id: String,
    pub name: Option<String>,

    #[serde(flatten)]
    pub platform_config: PlatformConfig,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct SensorConfig {
    pub platform: String,
    pub id: String,
    pub name: Option<String>,

    #[serde(flatten)]
    pub platform_config: PlatformConfig,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct LightConfig {
    pub platform: String,
    pub id: String,
    pub name: Option<String>,

    #[serde(flatten)]
    pub platform_config: PlatformConfig,
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(untagged)]
pub enum PlatformConfig {
    Gpio(GpioConfig),
    // Other platforms...
}

#[derive(Debug, Deserialize, Serialize)]
pub struct GpioConfig {
    pub pin: u8,

    #[serde(default)]
    pub inverted: bool,
}
