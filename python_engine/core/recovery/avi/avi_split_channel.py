import os
import struct

INPUT_FILE = "../../../sample_video/sample.avi"
OUTPUT_DIR = "../../../sample_output"

# 최대 허용 가능한 프레임 크기 (10MB)
MAX_REASONABLE_CHUNK_SIZE = 10 * 1024 * 1024

def extract_channel_by_signature(data, signature: bytes, valid_end: int):
    offset = 0
    count = 0
    extracted_chunks = []

    while offset < valid_end:
        index = data.find(signature, offset, valid_end)
        if index == -1:
            break

        if index + 8 > valid_end:
            break

        size_bytes = data[index + 4: index + 8]
        size = struct.unpack('<I', size_bytes)[0]

        chunk_start = index + 8
        chunk_end = chunk_start + size

        if size > MAX_REASONABLE_CHUNK_SIZE or chunk_end > valid_end:
            offset = index + 4
            continue

        if chunk_end - chunk_start < 5:
            offset = index + 4
            continue

        nal_prefix = data[chunk_start:chunk_start + 4]
        nal_type = data[chunk_start + 4] & 0x1F

        if nal_prefix != b'\x00\x00\x00\x01' or nal_type not in (1, 7):
            offset = index + 4
            continue

        extracted_chunks.append(data[chunk_start:chunk_end])
        count += 1
        offset = chunk_end

    return extracted_chunks, count

def split_normal_channels():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(INPUT_FILE, 'rb') as f:
        data = f.read()

    real_file_size = struct.unpack('<I', data[4:8])[0]
    valid_end = 8 + real_file_size  # RIFF 헤더 포함한 유효 구간

    # FRONT 채널 추출
    front_chunks, front_count = extract_channel_by_signature(data, b'00dc', valid_end)
    front_path = os.path.join(OUTPUT_DIR, 'normal_front.h264')
    with open(front_path, 'wb') as f:
        for chunk in front_chunks:
            f.write(chunk)

    # REAR 채널 추출
    rear_chunks, rear_count = extract_channel_by_signature(data, b'01dc', valid_end)
    rear_path = os.path.join(OUTPUT_DIR, 'normal_rear.h264')
    with open(rear_path, 'wb') as f:
        for chunk in rear_chunks:
            f.write(chunk)

    print(f"FRONT 채널: {front_count}개 프레임 → {front_path}")
    print(f"REAR 채널: {rear_count}개 프레임 → {rear_path}")

if __name__ == "__main__":
    split_normal_channels()