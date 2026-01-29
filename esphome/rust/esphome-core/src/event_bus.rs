use embassy_sync::pubsub::{PubSubChannel, Subscriber};
use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;

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
    channel: PubSubChannel<CriticalSectionRawMutex, SystemEvent, 8, 4, 2>,
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
    pub fn subscribe(&self) -> Subscriber<'_, CriticalSectionRawMutex, SystemEvent, 8, 4, 2> {
        self.channel.subscriber().unwrap()
    }
}

impl Default for EventBus {
    fn default() -> Self {
        Self::new()
    }
}
