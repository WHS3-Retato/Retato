import os
import struct

INPUT_FILE = r"E:\Retato\python_engine\sample_video\sample.avi"
OUTPUT_DIR = r"E:\Retato\python_engine\sample_output"

# 최대 허용 가능한 프레임 크기 (10MB)
MAX_REASONABLE_CHUNK_SIZE = 10 * 1024 * 1024

def extract_channel_by_signature(data, signature: bytes, valid_end: int):
    offset = 0
    count = 0
    extracted_chunks = []

    sps = pps = None # SPS, PPS 저장용

    while offset < valid_end:
        index = data.find(signature, offset, valid_end)
        if index == -1 or index + 8 > valid_end:
            break

        size = struct.unpack('<I', data[index + 4: index + 8])[0]
        chunk_start = index + 8
        chunk_end = chunk_start + size

        # 사이즈 검사
        if size > MAX_REASONABLE_CHUNK_SIZE or chunk_end > valid_end:
            offset = index + 4
            continue

        if chunk_end - chunk_start < 5:
            offset = index + 4
            continue

        # NAL 헤더 검사
        nal_prefix = data[chunk_start:chunk_start + 4]
        nal_type = data[chunk_start + 4] & 0x1F

        if nal_prefix != b'\x00\x00\x00\x01':
            offset = index + 4
            continue

        # SPS / PPS 저장
        if nal_type == 7:
            sps = data[chunk_start:chunk_end]
        elif nal_type == 8:
            pps = data[chunk_start:chunk_end]

        if nal_type in (1, 5, 7, 8):
            extracted_chunks.append(data[chunk_start:chunk_end])
            count += 1

        # 정렬 처리 (짝수 맞추기)
        aligned_size = size + (size % 2)
        offset = index + 8 + aligned_size

    return extracted_chunks, count, sps, pps

def write_chunks(filepath, chunks, sps=None, pps=None):
    with open(filepath, 'wb') as f:
        if sps and pps:
            f.write(sps)
            f.write(pps)
        for chunk in chunks:
            f.write(chunk)

def split_normal_channels():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(INPUT_FILE, 'rb') as f:
        data = f.read()

    real_file_size = struct.unpack('<I', data[4:8])[0]
    valid_end = 8 + real_file_size  # RIFF 헤더 포함한 유효 구간

    # FRONT 채널
    front_chunks, front_count, sps, pps = extract_channel_by_signature(data, b'00dc', valid_end)
    front_path = os.path.join(OUTPUT_DIR, 'normal_front.h264')
    write_chunks(front_path, front_chunks, sps, pps)

    # REAR 채널
    rear_chunks, rear_count, sps_r, pps_r = extract_channel_by_signature(data, b'01dc', valid_end)
    rear_path = os.path.join(OUTPUT_DIR, 'normal_rear.h264')
    write_chunks(rear_path, rear_chunks, sps_r, pps_r)

    print(f"FRONT 채널: {front_count}개 프레임 → {front_path}")
    print(f"REAR 채널: {rear_count}개 프레임 → {rear_path}")

if __name__ == "__main__":
    split_normal_channels()