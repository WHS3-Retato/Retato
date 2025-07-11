import os
import re
import struct
from python_engine.core.recovery.utils.ffmpeg_wrapper import convert_video

INPUT_DIR = r"E:\Retato\python_engine\sample_video"
OUTPUT_H264_DIR = r"E:\Retato\python_engine\sample_output\output_h264"
OUTPUT_VIDEO_DIR = r"E:\Retato\python_engine\sample_output\output_video"
TARGET_FORMAT = "mp4"

MAX_REASONABLE_CHUNK_SIZE = 10 * 1024 * 1024 # 10MB
MIN_VALID_BOX_SIZE = 8 # size + type
MIN_FRAME_SIZE = 5 # 너무 작은 프레임 필터링 기준

os.makedirs(OUTPUT_H264_DIR, exist_ok=True)
os.makedirs(OUTPUT_VIDEO_DIR, exist_ok=True)

def get_slack_after_moov(data):
    offset = 0
    while offset + MIN_VALID_BOX_SIZE <= len(data):
        try:
            size = struct.unpack('>I', data[offset:offset + 4])[0]
        except struct.error:
            print(f"[ERROR] size 언팩 실패 @ offset=0x{offset:X}")
            break

        box_type = data[offset + 4:offset + 8].decode("utf-8", errors="ignore")

        if box_type == "moov":
            return data[offset + size:], offset + size, data[offset:offset + size]
        
        if size <   MIN_VALID_BOX_SIZE:
            print(f"[WARNING] 비정상적인 박스 크기(size={size}) → 루프 종료 @ offset=0x{offset:X}")
            break

        offset += size

    return b'', None, None

def extract_sps_pps(moov_data):
    avcc_pos = moov_data.find(b'avcC')
    if avcc_pos == -1:
        print("[ERROR] avcC 박스를 찾을 수 없습니다.")
        return b''

    try:
        avcc_start = avcc_pos + 4
        sps_len = struct.unpack('>H', moov_data[avcc_start + 6:avcc_start + 8])[0]
        sps_start = avcc_start + 8
        sps = moov_data[sps_start:sps_start + sps_len]

        pps_len_start = sps_start + sps_len + 1
        pps_len = struct.unpack('>H', moov_data[pps_len_start:pps_len_start + 2])[0]
        pps_start = pps_len_start + 2
        pps = moov_data[pps_start:pps_start + pps_len]

        return b'\x00\x00\x00\x01' + sps + b'\x00\x00\x00\x01' + pps
    except (IndexError, struct.error) as e:
        print(f"[ERROR] SPS/PPS 추출 실패: {e}")
        return b''

def extract_frames(slack, slack_offset, sps_pps, output_h264_path):
    iframe_pattern = re.compile(b'\x00.{3}[\x25\x45\x65]\x88\x80')
    pframe_pattern = re.compile(b'\x00\x00.{2}[\x21\x41\x61]\x9A')
    
    matches = []
    for ftype, pattern in [("I", iframe_pattern), ("P", pframe_pattern)]:
        for m in pattern.finditer(slack):
            matches.append((m.start(), ftype))

    matches.sort(key=lambda x: x[0])

    has_i_frame = any(ftype == "I" for _, ftype in matches)
    if not any(ft == "I" for _, ft in matches) or len(matches) < 3:
        print("[INFO] 슬랙 영역이 존재하지 않거나 복원 가능한 데이터가 없습니다.")
        return 0
    
    recovered = 0
    with open(output_h264_path, 'wb') as f:
        f.write(sps_pps)
        for start, ftype in matches:
            try:
                size = struct.unpack('>I', slack[start:start + 4])[0]
                if size > MAX_REASONABLE_CHUNK_SIZE or size < MIN_FRAME_SIZE:
                    print(f"[WARNING] size={size} @ offset=0x{slack_offset + start:X} → skip")
                    continue

                end = start + 4 + size
                if end > len(slack):
                    print(f"[WARNING] 슬랙 초과 frame @ (offset=0x{slack_offset + start:X}")
                    continue

                f.write(b'\x00\x00\x00\x01' + slack[start + 4:end])
                print(f"[{ftype}-Frame] @ offset 0x{slack_offset + start:X}, size={size}")
                recovered += 1
            except (struct.error, IndexError):
                continue

    return recovered

def process_mp4_file(filepath):
    filename = os.path.splitext(os.path.basename(filepath))[0]
    h264_path = os.path.join(OUTPUT_H264_DIR, f"{filename}_slack.h264")
    mp4_path = os.path.join(OUTPUT_VIDEO_DIR, f"{filename}_slack.{TARGET_FORMAT}")

    with open(filepath, 'rb') as f:
        data = f.read()

    slack, slack_offset, moov_data = get_slack_after_moov(data)
    if slack_offset is None:
        print(f"[ERROR] {filename} → moov 박스 없음 → skip")
        return
    
    print(f"[INFO] 슬랙 영역 시작 offset: 0x{slack_offset:X}")
    sps_pps = extract_sps_pps(moov_data)
    if not sps_pps:
        print(f"[ERROR] {filename} → SPS/PPS 추출 실패 → skip")
        return
    
    count = extract_frames(slack, slack_offset, sps_pps, h264_path)
    print(f"[INFO] 복구된 프레임 수: {count}개 → {h264_path}")

    if count > 0:
        convert_video(h264_path, mp4_path, TARGET_FORMAT)
    else:
        print(f"[SKIP] {filename} → 유효한 프레임이 없어 변환 생략")

def extract_slack_from_all_mp4():
    for file in os.listdir(INPUT_DIR):
        if file.lower().endswith('.mp4'):
            print(f"\n[INFO] MP4 파일 처리 중: {file}")
            process_mp4_file(os.path.join(INPUT_DIR, file))

if __name__ == "__main__":
    extract_slack_from_all_mp4()