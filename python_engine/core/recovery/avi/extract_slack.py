import os
import struct
from python_engine.core.recovery.utils.ffmpeg_wrapper import convert_video

INPUT_DIR = r"E:\Retato\python_engine\sample_video"
OUTPUT_H264_DIR = r"E:\Retato\python_engine\sample_output\output_h264"
OUTPUT_VIDEO_DIR = r"E:\Retato\python_engine\sample_output\output_video"
TARGET_FORMAT = "mp4"
MAX_REASONABLE_CHUNK_SIZE = 10 * 1024 * 1024

FRONT_SIGNATURE = b'00dc'
REAR_SIGNATURE = b'01dc'

os.makedirs(OUTPUT_H264_DIR, exist_ok=True)
os.makedirs(OUTPUT_VIDEO_DIR, exist_ok=True)

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
            print(f"[WARNING] 비정상적으로 큰 프레임 (size={size}, offset=0x{index:X})")
            offset = index + 4
            continue
        if size < 5:
            print(f"[WARNING] 너무 작은 프레임 (size={size}, offset=0x{index:X})")
            offset = index + 4
            continue
        if chunk_end > end:
            print(f"[WARNING] 프레임이 파일 끝을 넘어감 (size={size}, offset=0x{index:X})")
            offset = index + 4
            continue

        # NAL 검사
        if data[chunk_start:chunk_start + 4] != b'\x00\x00\x00\x01':
            print(f"[WARNING] 잘못된 NAL prefix (offset=0x{index:X})")
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

    return chunks, count, sps, pps

def write_chunks(filepath, chunks, sps=None, pps=None):
    with open(filepath, 'wb') as f:
        if sps and pps:
            f.write(sps)
            f.write(pps)
        for chunk in chunks:
            f.write(chunk)

def process_slack_from_file(filepath):
    filename = os.path.splitext(os.path.basename(filepath))[0]
    with open(filepath, 'rb') as f:
        data = f.read()

    try:
        riff_size = struct.unpack('<I', data[4:8])[0]
        slack_start = 8 + riff_size
    except:
        print(f"[ERROR] {filename} RIFF 파싱 실패 → 건너뜀")
        return
    
    for label, sig in [('slack_front', b'00dc'), ('slack_rear', b'01dc')]:
        chunks, count, sps, pps = extract_channel_from_slack(data, slack_start, sig)
        h264_path = os.path.join(OUTPUT_H264_DIR, f"{filename}_{label}.h264")
        mp4_path = os.path.join(OUTPUT_VIDEO_DIR, f"{filename}_{label}.{TARGET_FORMAT}")
        
        write_chunks(h264_path, chunks, sps, pps)
        print(f"[INFO] {label.upper()} 채널: {count}개 프레임 → {h264_path}")

        if count > 0:
            convert_video(h264_path, mp4_path, TARGET_FORMAT)
        else:
            print(f"[SKIP] {label.upper()} 채널은 유효한 프레임이 없어 변환 생략")

def extract_slack_from_all_files():
    for file in os.listdir(INPUT_DIR):
        if file.lower().endswith('.avi'):
            filepath = os.path.join(INPUT_DIR, file)
            print(f"\n[INFO] AVI 파일 처리 중: {file}")
            process_slack_from_file(filepath)

if __name__ == "__main__":
    extract_slack_from_all_files()