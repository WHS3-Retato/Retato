import os
import struct

INPUT_FILE = r"E:\Retato\python_engine\sample_video\sample.avi"
OUTPUT_DIR = r"E:\Retato\python_engine\sample_output"
MAX_REASONABLE_CHUNK_SIZE = 10 * 1024 * 1024

# 경로 유효성 검사
if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(f"입력 파일 경로가 존재하지 않습니다: {INPUT_FILE}")

if not os.path.isdir(OUTPUT_DIR):
    try:
        os.makedirs(OUTPUT_DIR)
    except Exception as e:
        raise RuntimeError(f"출력 디렉토리 생성 실패: {OUTPUT_DIR}\n원인: {e}")

def extract_channel_from_slack(data, start_offset, signature):
    offset = start_offset
    end = len(data)
    chunks = []
    sps = pps = None
    count = 0

    while offset < end - 8:
        index = data.find(signature, offset, end)
        if index == -1 or index + 8 > end:
            break

        try:
            size = struct.unpack('<I', data[index + 4: index + 8])[0]
        except:
            offset = index + 1
            continue

        chunk_start = index + 8
        chunk_end = chunk_start + size
        aligned = size + (size % 2)

        # 프레임 크기 유효성 검사
        if size > MAX_REASONABLE_CHUNK_SIZE:
            print(f"[경고] 비정상적으로 큰 프레임 (size={size}, offset=0x{index:X})")
            offset = index + 4
            continue
        if size < 5:
            print(f"[경고] 너무 작은 프레임 (size={size}, offset=0x{index:X})")
            offset = index + 4
            continue
        if chunk_end > end:
            print(f"[경고] 프레임이 파일 끝을 넘어감 (size={size}, offset=0x{index:X})")
            offset = index + 4
            continue

        # NAL 검사
        if not (data[chunk_start:chunk_start + 4] == b'\x00\x00\x00\x01'):
            print(f"[경고] 잘못된 NAL prefix (offset=0x{index:X})")
            offset = index + 4
            continue

        nal_type = data[chunk_start + 4] & 0x1F
        frame = data[chunk_start:chunk_end]

        if nal_type == 7 and sps is None:
            sps = frame
        elif nal_type == 8 and pps is None:
            pps = frame

        if nal_type in (1, 5, 7, 8):
            chunks.append(frame)
            count += 1

        offset = index + 8 + aligned

    return chunks, sps, pps, count

def write_h264(path, frames, sps, pps):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        if sps: f.write(sps)
        if pps: f.write(pps)
        for frame in frames:
            f.write(frame)

def extract_slack_from_file():
    with open(INPUT_FILE, 'rb') as f:
        data = f.read()

    riff_size = struct.unpack('<I', data[4:8])[0]
    slack_start = 8 + riff_size
    print(f"[info] 슬랙 탐색 시작 offset: 0x{slack_start:X} ({slack_start:,} bytes)")

    # FRONT
    front, sps_f, pps_f, count_f = extract_channel_from_slack(data, slack_start, b'00dc')
    if count_f:
        front_path = os.path.join(OUTPUT_DIR, 'avi-slack_front.h264')
        write_h264(front_path, front, sps_f, pps_f)
        print(f"front 채널: {count_f}개 슬랙 프레임 → {front_path}")
    else:
        print("front 채널: 슬랙 프레임 없음")

    # REAR
    rear, sps_r, pps_r, count_r = extract_channel_from_slack(data, slack_start, b'01dc')
    if count_r:
        rear_path = os.path.join(OUTPUT_DIR, 'slack_rear.h264')
        write_h264(rear_path, rear, sps_r, pps_r)
        print(f"rear 채널: {count_r}개 슬랙 프레임 → {rear_path}")
    else:
        print("rear 채널: 슬랙 프레임 없음")

if __name__ == "__main__":
    extract_slack_from_file()