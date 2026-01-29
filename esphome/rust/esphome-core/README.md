# esphome-core (Rust)

**Status**: Alpha / Foundation

## Deficiencies & Remaining Work

### 1. Component State Registry
- **Problem**: There is no global registry to look up components by ID or iterate through them for global operations.
- **Work**: Implement a thread-safe registry (likely using a static map or linked list) to track all active `Component` instances.

### 2. Standardized Communication
- **Problem**: While `ActorAddress` exists, there is no standardized way to map YAML "automations" (actions/triggers) to these addresses at code-gen time.
- **Work**: Enhance the generator to wire component events to actions in other components.
