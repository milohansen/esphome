# esphome-ota (Rust)

**Status**: Proof of Concept / Alpha

## Deficiencies & Remaining Work

### 1. Partition Management (CRITICAL)
- **Problem**: The current implementation blindly picks the first OTA partition it finds or assumes a layout. It does not read the `otadata` partition to determine the currently active slot.
- **Risk**: Overwriting the partition currently being executed, leading to immediate crash and possible corruption.
- **Work**: Implement robust parsing of the `esp-idf` partition table and the `otadata` structure (sequence numbers, CRC check) to safely identify the target partition.

### 2. Protocol Completeness
- **Problem**: Implements a minimal handshake. It does not support:
    - **Authentication**: Password checking is currently skipped.
    - **Version Negotiation**: Does not verify protocol version compatibility with the client.
    - **Progress Feedback**: Does not send back progress bytes to the client.
- **Work**: Align with the ESPHome C++ OTA protocol state machine.

### 3. Hardware Support
- **Problem**: Tested only for ESP32 standard flash.
- **Work**: Verify behavior on ESP32-C3/S3 and handle different sector sizes if applicable. Ensure `esp-storage` correctly handles page/sector erasure before writing.

### 4. Post-Update Actions
- **Problem**: The device does not automatically reboot or set the boot flag in `otadata` after a successful write.
- **Work**: Implement the logic to update the `otadata` sequence number and trigger a system reset (`esp_hal::reset::software_reset`).
