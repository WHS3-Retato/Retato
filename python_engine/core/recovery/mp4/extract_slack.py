import os
import re
import struct

INPUT_FILE = r"E:\Retato\python_engine\sample_video\mp4_sample.mp4"
OUTPUT_DIR = r"E:\Retato\python_engine\sample_output"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "mp4_extract_slack.h264") 

MAX_REASONABLE_CHUNK_SIZE = 10 * 1024 * 1024  # 10MB
MIN_VALID_BOX_SIZE = 8 # size + type
MIN_FRAME_SIZE = 5 # 너무 작은 프레임 필터링 기준

def get_slack_after_moov(path):
    try:
        with open(path, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        print(f"[ERROR] 입력 파일을 찾을 수 없습니다: {path}")
        return b'', None, None

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
            print(f"[WARNING]] 비정상적인 박스 크기(size={size}) → 루프 종료 @ offset=0x{offset:X}")
            break

        offset += size

    return b'', None, None

def extract_sps_pps(moov_data):
    if moov_data is None:
        print("[ERROR] moov 박스가 존재하지 않습니다.")
        return b''

    avcc_pos = moov_data.find(b'avcC')
    if avcc_pos == -1:
        print("[ERROR] avcC 박스를 찾을 수 없습니다.")
        return b''

    avcc_start = avcc_pos + 4

    try:
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

def recover_from_slack(mp4_path, output_path):
    slack, slack_offset, moov_data = get_slack_after_moov(mp4_path)
    if slack_offset is None:
        print("[ERROR] moov 박스를 찾을 수 없습니다.")
        return

    print(f"[INFO] 슬랙 영역 시작 offset: 0x{slack_offset:x}")

    if not slack:
        print("[INFO] 슬랙 영역이 존재하지 않거나 복원 가능한 데이터가 없습니다.")
        return

    sps_pps = extract_sps_pps(moov_data)
    if not sps_pps:
        print("[ERROR] SPS/PPS 추출 실패")
        return

    iframe_pattern = re.compile(b'\x00.{3}[\x25\x45\x65]\x88\x80')
    pframe_pattern = re.compile(b'\x00\x00.{2}[\x21\x41\x61]\x9A')

    matches = []
    for ftype, pattern in [("I", iframe_pattern), ("P", pframe_pattern)]:
        for m in pattern.finditer(slack):
            matches.append((m.start(), ftype))

    matches.sort(key=lambda x: x[0])

    has_i_frame = any(ftype == "I" for _, ftype in matches)
    if not has_i_frame or len(matches) < 3:
        print("[INFO] 슬랙 영역이 존재하지 않거나 복원 가능한 데이터가 없습니다.")
        return

    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    except PermissionError:
        print("[ERROR] 출력 디렉토리를 생성할 수 없습니다")
        return
    
    recovered = 0
    with open(output_path, 'wb') as f:
        f.write(sps_pps)
        for start, ftype in matches:
            try:
                size = struct.unpack('>I', slack[start:start + 4])[0]
                if size > MAX_REASONABLE_CHUNK_SIZE:
                    print(f"[WARNING] 너무 큰 프레임 size={size} @ offset=0x{slack_offset + start:X}")
                    continue
                if size < MIN_FRAME_SIZE:
                    print(f"[WARNING] 너무 작은 프레임 size={size} @ offset=0x{slack_offset + start:X}")
                    continue

                end = start + 4 + size
                if end > len(slack):
                    print(f"[WARNING] 프레임이 슬랙 영역을 초과함 (offset=0x{slack_offset + start:X}, size={size})")
                    continue

                f.write(b'\x00\x00\x00\x01' + slack[start + 4:end])
                print(f"[{ftype}-Frame] @ offset 0x{slack_offset + start:X}, size={size}")
                recovered += 1
            except (struct.error, IndexError):
                continue

    print(f"[INFO] 총 {recovered}개 프레임 저장 완료 → {output_path}")

if __name__ == "__main__":
    recover_from_slack(INPUT_FILE, OUTPUT_FILE)