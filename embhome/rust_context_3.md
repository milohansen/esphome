### Project Context & Goal

The objective is to enable a **hybrid build system** for ESPHome that compiles C++ framework libraries via PlatformIO and links them into a Rust application managed by Cargo. The current target is the **ESP32-C3 (RISC-V)**, which has introduced specific architectural challenges regarding linker flags and memory mapping.

### Summary of Changes & Progress

Debugging has focused on `rust_generator.py`, the script responsible for automating the build lifecycle.

**1. Linker Script Management (Fixing Memory Layout)**

* **Issue:** The build failed with "memory region not declared" and "undefined symbol" errors (e.g., `TIMERG0`). This was because the script was missing `peripherals.ld` (which defines hardware addresses) and had excluded `memory.ld` to avoid conflicts.
* **Fix:**
* Implemented recursive search to locate `peripherals.ld` (or `esp32c3.peripherals.ld`) within the ESP-IDF framework packages.
* Re-enabled `memory.ld` but added a patching step to create `memory_fixed.ld`. This removes conflicting `REGION_ALIAS` directives while keeping the essential memory region definitions required by the binary blobs.
* Enforced a strict linker script order: `memory`  `peripherals`  `sections`.



**2. RISC-V Specific Compilation**

* **Issue:** "Relocation truncated to fit" errors indicated that jump instructions were trying to reach addresses too far away (a common RISC-V issue when memory layouts are incorrect or relaxation is disabled).
* **Fix:** Added the `-mrelax` linker flag (replacing the unsupported `--relax`) to the Cargo configuration to enable linker relaxation for RISC-V.

**3. Resolving Circular Dependencies & Missing Symbols**

* **Issue:** The linker reported undefined references to low-level interrupt functions like `esprv_int_set_priority`, even though the libraries were present. The linker was discarding them as "unused" before encountering the code that needed them.
* **Fix:**
* Updated `build.rs` to wrap all static libraries in a `--start-group` / `--end-group` block.
* Added `rustc-link-arg=-u <symbol>` flags to explicitly force the linker to include the missing interrupt symbols (`esprv_int_...`).



### Current Status

The `rust_generator.py` script has been fully updated to address the linker script ordering, file discovery, and symbol forcing. The next step is to run this updated script and verify if the `undefined reference` and `relocation truncated` errors have been resolved.
