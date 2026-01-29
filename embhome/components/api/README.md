# esphome-api (Rust)

**Status**: Alpha / Functional Handshake

## Deficiencies & Remaining Work

### 1. Proto Definition Coverage
- **Problem**: Only a subset of messages from `api.proto` are implemented in the server's `handle_frame` logic (Hello, Connect, Ping).
- **Work**: Implement handlers for:
    - `ListEntitiesRequest` (Discovery)
    - `SubscribeStatesRequest` (Updates)
    - Component-specific commands (Switch, Light, etc.)

### 2. State Publishing
- **Problem**: There is currently no mechanism for components to push state changes (e.g., sensor readings) back through the API server to Home Assistant.
- **Work**: Create a shared state registry or event bus bridge that the API server can use to broadcast messages.

### 3. Encryption (Noise Protocol)
- **Problem**: Only plaintext communication is currently supported.
- **Work**: Integrate the Noise protocol for secure communication with Home Assistant.
