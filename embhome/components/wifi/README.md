# esphome-wifi (Rust)

**Status**: Alpha / Functional

## Deficiencies & Remaining Work

### 1. Advanced WiFi Features
- **Problem**: No support for:
    - **Static IP**: Currently hardcoded to DHCP.
    - **Hidden SSIDs**: Not handled.
    - **Captive Portal**: No fallback AP mode implemented.
- **Work**: Expand `WifiConfig` and `connection_task` to handle fallback scenarios.

### 2. Stack Stability
- **Problem**: Reconnection logic is simplistic.
- **Work**: Implement exponential backoff and better handling of transient radio errors.
