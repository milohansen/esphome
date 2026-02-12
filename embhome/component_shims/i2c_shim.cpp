#include <cstdint>
#include <cstring>
#include <stddef.h>

// Rust FFI functions for I2C operations
extern "C" {
    int rust_i2c_write(uint8_t addr, const uint8_t* data, size_t len);
    int rust_i2c_read(uint8_t addr, uint8_t* buffer, size_t len);
    int rust_i2c_write_read(
        uint8_t addr,
        const uint8_t* write_data,
        size_t write_len,
        uint8_t* read_buffer,
        size_t read_len
    );
}

// Wire-compatible shim class that delegates to Rust async I2C
class I2CShim {
public:
    void begin(int sda, int scl) {
        // No-op: Rust already initialized the bus
    }

    void beginTransmission(uint8_t addr) {
        current_addr = addr;
        write_buffer_len = 0;
    }

    size_t write(uint8_t data) {
        if (write_buffer_len < sizeof(write_buffer)) {
            write_buffer[write_buffer_len++] = data;
            return 1;
        }
        return 0;
    }

    size_t write(const uint8_t* data, size_t len) {
        size_t written = 0;
        for (size_t i = 0; i < len && write_buffer_len < sizeof(write_buffer); i++) {
            write_buffer[write_buffer_len++] = data[i];
            written++;
        }
        return written;
    }

    uint8_t endTransmission(bool stop = true) {
        // Call Rust async I2C - this BLOCKS the calling C++ task
        int result = rust_i2c_write(current_addr, write_buffer, write_buffer_len);
        write_buffer_len = 0;
        return (result == 0) ? 0 : 4;  // 0 = success, 4 = error
    }

    size_t requestFrom(uint8_t addr, size_t len, bool stop = true) {
        // Call Rust async I2C - this BLOCKS
        int result = rust_i2c_read(addr, read_buffer, len);
        if (result == 0) {
            read_buffer_len = len;
            read_buffer_pos = 0;
            return len;
        }
        return 0;
    }

    int available() {
        return read_buffer_len - read_buffer_pos;
    }

    int read() {
        if (read_buffer_pos < read_buffer_len) {
            return read_buffer[read_buffer_pos++];
        }
        return -1;
    }

private:
    uint8_t current_addr = 0;
    uint8_t write_buffer[128];
    size_t write_buffer_len = 0;
    uint8_t read_buffer[128];
    size_t read_buffer_len = 0;
    size_t read_buffer_pos = 0;
};

// Global Wire instance (replaces Arduino's Wire)
I2CShim Wire;
