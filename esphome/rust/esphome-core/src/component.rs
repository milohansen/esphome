use embassy_sync::channel::{Receiver, Sender};
use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;

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
    async fn run(&mut self, mailbox: Receiver<'static, CriticalSectionRawMutex, Self::Message, 8>);
}

/// Component errors
#[derive(Debug)]
pub enum ComponentError {
    HardwareError(&'static str),
    ConfigError(&'static str),
    CommunicationError(&'static str),
}

/// Type-safe address to a component's mailbox
pub struct ActorAddress<M: Send> {
    sender: Sender<'static, CriticalSectionRawMutex, M, 8>,
}

impl<M: Send> ActorAddress<M> {
    pub fn new(sender: Sender<'static, CriticalSectionRawMutex, M, 8>) -> Self {
        Self { sender }
    }

    /// Send message (blocks if mailbox full)
    pub async fn send(&self, message: M) {
        self.sender.send(message).await;
    }

    /// Try to send message (fails if mailbox full)
    pub fn try_send(&self, message: M) -> Result<(), embassy_sync::channel::TrySendError<M>> {
        self.sender.try_send(message)
    }
}

impl<M: Send> Clone for ActorAddress<M> {
    fn clone(&self) -> Self {
        Self { sender: self.sender.clone() }
    }
}
