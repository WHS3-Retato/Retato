import os
import struct
from python_engine.core.recovery.utils.ffmpeg_wrapper import convert_video

# 경로지정
INPUT_DIR = r"E:\Retato\python_engine\sample_video"
OUTPUT_H264_DIR = r"E:\Retato\python_engine\sample_output\output_h264"
OUTPUT_VIDEO_DIR = r"E:\Retato\python_engine\sample_output\output_video"
TARGET_FORMAT = "mp4"

# 최대 허용 가능한 프레임 크기 (10MB)
MAX_REASONABLE_CHUNK_SIZE = 10 * 1024 * 1024

# 전/후방 시그니처
FRONT_SIGNATURE = b'00dc'
REAR_SIGNATURE = b'01dc'

# 출력 디렉토리 생성
os.makedirs(OUTPUT_H264_DIR, exist_ok=True)
os.makedirs(OUTPUT_VIDEO_DIR, exist_ok=True)

def extract_channel_by_signature(data, signature, valid_end):
    offset = 0
    count = 0
    extracted_chunks = []
    sps = pps = None # SPS, PPS 저장용

    while offset < valid_end:
        index = data.find(signature, offset, valid_end)
        if index == -1 or index + 8 > valid_end:
            break

        size = struct.unpack('<I', data[index + 4:index + 8])[0]

        chunk_start = index + 8
        chunk_end = chunk_start + size

        # 사이즈 검사
        if size > MAX_REASONABLE_CHUNK_SIZE:
            print(f"[WARNING] 비정상적으로 큰 프레임 (size={size}, offset=0x{index:X})")
            offset = index + 4
            continue

        if chunk_end - chunk_start < 5:
            print(f"[WARNING] 너무 작은 프레임 (size={size}, offset=0x{index:X})")
            offset = index + 4
            continue

        if chunk_end > valid_end:
            print(f"[WARNING] 프레임이 파일 끝을 넘어감 (size={size}, offset=0x{index:X})")
            offset = index + 4
            continue

        # NAL 헤더 검사
        nal_prefix = data[chunk_start:chunk_start + 4]
        if nal_prefix != b'\x00\x00\x00\x01':
            print(f"[WARNING] 잘못된 NAL prefix (offset=0x{index:X})")
            offset = index + 4
            continue
        
        # SPS / PPS 저장
        nal_type = data[chunk_start + 4] & 0x1F
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


def process_avi_file(filepath):
    filename = os.path.splitext(os.path.basename(filepath))[0]
    with open(filepath, 'rb') as f:
        data = f.read()

    try:
        real_file_size = struct.unpack('<I', data[4:8])[0]
        valid_end = 8 + real_file_size
    except struct.error:
        print(f"[ERROR] RIFF size 파싱 실패: {filepath}")
        return
    
    for label, sig in [('front', FRONT_SIGNATURE), ('rear', REAR_SIGNATURE)]:
        chunks, count, sps, pps = extract_channel_by_signature(data, sig, valid_end)
        h264_path = os.path.join(OUTPUT_H264_DIR, f"{filename}_{label}.h264")
        mp4_path = os.path.join(OUTPUT_VIDEO_DIR, f"{filename}_{label}.{TARGET_FORMAT}")

        write_chunks(h264_path, chunks, sps, pps)
        print(f"[INFO] {label.upper()} 채널: {count}개 프레임 → {h264_path}")

        if count > 0:
            convert_video(h264_path, mp4_path, TARGET_FORMAT)
        else:
            print(f"[SKIP] {label.upper()} 채널은 유효한 프레임이 없어 변환 생략")

def split_all_avi_files():
    for file in os.listdir(INPUT_DIR):
        if file.lower().endswith(".avi"):
            filepath = os.path.join(INPUT_DIR, file)
            print(f"\n[INFO] AVI 파일 처리 중: {file}")
            process_avi_file(filepath)

if __name__ == "__main__":
    split_all_avi_files()