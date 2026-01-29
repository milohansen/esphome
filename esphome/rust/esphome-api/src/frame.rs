use prost::decode_length_delimiter;
use prost::encode_length_delimiter;
use alloc::vec::Vec;

pub enum FrameError {
    Incomplete,
    TooLarge,
    Invalid,
}

pub struct Frame {
    pub msg_type: u32,
    pub payload: Vec<u8>,
}

pub fn decode_frame(data: &[u8]) -> Result<(Frame, usize), FrameError> {
    if data.is_empty() || data[0] != 0x00 {
         // ESPHome frames always start with 0x00 (reserved)
         // Wait, actually the format is:
         // 0x00 (reserved)
         // varint length
         // varint msg_type
         // payload
    }

    if data.len() < 3 {
        return Err(FrameError::Incomplete);
    }

    let mut offset = 1; // Skip reserved 0x00

    let length = decode_length_delimiter(&data[offset..]).map_err(|_| FrameError::Invalid)?;
    let length_size = prost::length_delimiter_len(length);
    offset += length_size;

    let msg_type = decode_length_delimiter(&data[offset..]).map_err(|_| FrameError::Invalid)?;
    let msg_type_size = prost::length_delimiter_len(msg_type);
    offset += msg_type_size;

    let payload_len = length as usize - msg_type_size;

    if data.len() < offset + payload_len {
        return Err(FrameError.Incomplete);
    }

    let frame = Frame {
        msg_type: msg_type as u32,
        payload: data[offset..offset + payload_len].to_vec(),
    };

    Ok((frame, offset + payload_len))
}

pub fn encode_frame(msg_type: u32, payload: &[u8]) -> Vec<u8> {
    let mut buf = Vec::new();
    buf.push(0x00);

    let msg_type_size = prost::length_delimiter_len(msg_type as usize);
    let total_len = msg_type_size + payload.len();

    let mut len_buf = [0u8; 10];
    encode_length_delimiter(total_len, &mut len_buf).unwrap();
    buf.extend_from_slice(&len_buf[..prost::length_delimiter_len(total_len)]);

    encode_length_delimiter(msg_type as usize, &mut len_buf).unwrap();
    buf.extend_from_slice(&len_buf[..msg_type_size]);

    buf.extend_from_slice(payload);
    buf
}
