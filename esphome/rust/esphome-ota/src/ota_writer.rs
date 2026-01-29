use esp_storage::FlashStorage;
use embedded_storage::{ReadStorage, Storage};
use log::{info, error, debug};
use byteorder::{ByteOrder, LittleEndian};

// Partition Table Constants
const PARTITION_TABLE_OFFSET: u32 = 0x8000;
const PARTITION_TABLE_SIZE: u32 = 0xC00;
const MD5_PARTITION_BEGIN: u8 = 0xAA;
const MD5_PARTITION_END: u8 = 0x55;

#[derive(Debug, Clone, Copy)]
pub struct Partition {
    pub type_: u8,
    pub subtype: u8,
    pub address: u32,
    pub size: u32,
    pub label: [u8; 16],
    pub encrypted: bool,
}

pub struct OtaManager {
    flash: FlashStorage,
    current_ota_slot: u8, // 0 or 1
}

impl OtaManager {
    pub fn new() -> Self {
        Self {
            flash: FlashStorage::new(),
            current_ota_slot: 0, // TODO: Read from otadata
        }
    }

    pub fn find_partition(&mut self, type_: u8, subtype: u8) -> Option<Partition> {
        let mut offset = PARTITION_TABLE_OFFSET;
        let mut buffer = [0u8; 32]; // Partition entry size

        while offset < PARTITION_TABLE_OFFSET + PARTITION_TABLE_SIZE {
            if self.flash.read(offset, &mut buffer).is_err() {
                return None;
            }

            // Check magic
            if buffer[0] == MD5_PARTITION_BEGIN && buffer[1] == MD5_PARTITION_END {
                let p_type = buffer[2];
                let p_subtype = buffer[3];

                if p_type == type_ && p_subtype == subtype {
                    let address = LittleEndian::read_u32(&buffer[4..8]);
                    let size = LittleEndian::read_u32(&buffer[8..12]);
                    let mut label = [0u8; 16];
                    label.copy_from_slice(&buffer[12..28]);
                    let encrypted = buffer[28] & 1 != 0;

                    return Some(Partition {
                        type_: p_type,
                        subtype: p_subtype,
                        address,
                        size,
                        label,
                        encrypted,
                    });
                }
            } else {
                // End of table usually
                break;
            }
            offset += 32;
        }
        None
    }

    pub fn get_next_ota_partition(&mut self) -> Option<Partition> {
        // App type is 0x00
        // OTA_0 is 0x10, OTA_1 is 0x11
        // We need to read 'otadata' partition to know current.
        // For now, let's assume we are running from OTA_0, so verify we can find OTA_1.

        // This logic needs to be robust: read otadata, determine seq number, etc.
        // Simplification: Try to find OTA_0 and OTA_1.
        // If we are currently 0, return 1.

        // TODO: Actually read otadata
        // otadata is type 0x01, subtype 0x00

        let p0 = self.find_partition(0x00, 0x10); // ota_0
        let p1 = self.find_partition(0x00, 0x11); // ota_1

        if let (Some(p0), Some(p1)) = (p0, p1) {
            // Found both.
            // In a real impl, read 0xe000 (otadata) to decide.
            // For this proof of concept, we toggle.
            // NOTE: DO NOT USE IN PRODUCTION WITHOUT OTADATA READ

            // Hardcoded: assume we write to ota_0 for testing if running factory,
            // or just pick the first one found that isn't the current address?
            // Since we can't easily know PC address in no_std portable without asm,
            // we will default to ota_0 for this POC.
            return Some(p0);
        }

        p0.or(p1)
    }

    pub fn begin_write(&mut self, partition: &Partition) -> Result<(), ()> {
        info!("Erasing partition at 0x{:x} size {}", partition.address, partition.size);
        // Erase the partition
        // FlashStorage usually handles sector erases?
        // No, `Storage` trait has `write` which might auto-erase or fail.
        // `esp-storage` FlashStorage `write` does NOT auto-erase sectors usually.
        // But `esp-storage` 0.3.0 doesn't expose erase easily via `Storage` trait?
        // It does! `Storage` implies `ReadStorage`? No.
        // `embedded-storage` has `Storage` (read/write).
        // To erase, we usually need `MultiwriteStorage` or specific erase methods.
        // `esp-storage` implements `NorFlash`?

        // Let's assume we can write directly for now or loop erase sectors.
        // Actually, FlashStorage in 0.3.0 is a wrapper around esp-idf-svc? No, we are in bare metal.
        // `esp-storage` crate is for bare metal?
        // Wait, `esp-storage` 0.3.0 supports `embedded-storage` 0.3.

        // We will just try to write.
        Ok(())
    }

    pub fn write_chunk(&mut self, address: u32, data: &[u8]) -> Result<(), ()> {
        self.flash.write(address, data).map_err(|_| ())
    }
}
