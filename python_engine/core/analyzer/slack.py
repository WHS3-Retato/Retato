import struct
import os

def analyze_mp4_slack(file_path):
    with open(file_path, 'rb') as f:
        mp4 = f.read()

    file_size = len(mp4)
    cursor = 0
    slack_regions = []
    total_valid = 0
    last_box_end = 0

    while cursor + 8 <= file_size:
        size_bytes = mp4[cursor:cursor+4]
        type_bytes = mp4[cursor+4:cursor+8]

        try:
            size = int.from_bytes(size_bytes, 'big')
            box_type = type_bytes.decode('utf-8', errors='ignore')
        except:
            break

        if size < 8 or cursor + size > file_size:
            break

        box_start = cursor
        box_end = cursor + size

        # 내부 슬랙 탐지: 이전 박스 끝 ~ 현재 박스 시작 간의 빈 공간
        if box_start > last_box_end:
            slack_regions.append((last_box_end, box_start))

        total_valid += size
        last_box_end = box_end
        cursor = box_end

    # EOF 이후 슬랙
    if last_box_end < file_size:
        slack_regions.append((last_box_end, file_size))

    slack_bytes = sum(end - start for start, end in slack_regions)
    slack_ratio = (slack_bytes / file_size) * 100

    return {
        "total_bytes": file_size,
        "valid_data_bytes": file_size - slack_bytes,
        "slack_bytes": slack_bytes,
        "slack_ratio_percent": round(slack_ratio, 2),
        "slack_regions": slack_regions
    }

def analyze_avi_slack(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()

    file_size = len(data)

    if data[:4] != b'RIFF':
        raise ValueError("Invalid AVI file: Missing RIFF header")

    riff_size = int.from_bytes(data[4:8], 'little')
    riff_end = 8 + riff_size

    cursor = 12
    slack_regions = []
    total_valid = 0
    last_chunk_end = cursor

    while cursor + 8 <= file_size:
        chunk_start = cursor
        chunk_id = data[cursor:cursor+4]

        try:
            chunk_size = struct.unpack('<I', data[cursor+4:cursor+8])[0]
        except:
            break

        chunk_end = cursor + 8 + chunk_size
        if chunk_end > file_size:
            break

        # 슬랙 감지: 이전 청크 끝과 현재 청크 시작 간 gap
        if chunk_start > last_chunk_end:
            slack_regions.append((last_chunk_end, chunk_start))

        total_valid += (chunk_end - chunk_start)
        last_chunk_end = chunk_end
        cursor = chunk_end

        if chunk_size % 2 == 1:
            cursor += 1
            last_chunk_end += 1

    if riff_end < file_size:
        slack_regions.append((riff_end, file_size))

    slack_bytes = sum(end - start for start, end in slack_regions)
    slack_ratio = (slack_bytes / file_size) * 100

    return {
        "total_bytes": file_size,
        "valid_data_bytes": file_size - slack_bytes,
        "slack_bytes": slack_bytes,
        "slack_ratio_percent": round(slack_ratio, 2),
        "slack_regions": slack_regions
    }
