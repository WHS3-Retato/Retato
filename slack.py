import struct

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

    # RIFF 헤더 확인 및 전체 사이즈 계산
    if data[:4] != b'RIFF':
        raise ValueError("Invalid AVI file: Missing RIFF header")

    riff_size = int.from_bytes(data[4:8], 'little')
    riff_end = 8 + riff_size  # 정상적으로 정의된 파일 끝 위치

    # movi 섹션 탐색
    movi_offset = data.find(b'movi')
    if movi_offset == -1:
        raise ValueError("No 'movi' section found")

    cursor = movi_offset + 4
    chunk_headers = [b'00dc', b'01dc', b'00db', b'01db']
    slack_regions = []
    total_valid = 0
    last_chunk_end = cursor

    while cursor + 8 <= file_size:
        chunk_id = data[cursor:cursor+4]
        if chunk_id not in chunk_headers:
            # 슬랙 영역 시작
            slack_start = cursor
            while cursor + 8 <= file_size:
                possible_id = data[cursor:cursor+4]
                if possible_id in chunk_headers:
                    break
                cursor += 1
            slack_regions.append((slack_start, cursor))
            last_chunk_end = cursor
            continue

        try:
            chunk_size = struct.unpack('<I', data[cursor+4:cursor+8])[0]
        except:
            break

        chunk_end = cursor + 8 + chunk_size
        if chunk_end > file_size:
            break

        # 내부 슬랙 감지
        if cursor > last_chunk_end:
            slack_regions.append((last_chunk_end, cursor))

        total_valid += (chunk_end - cursor)
        last_chunk_end = chunk_end
        cursor = chunk_end

    # EOF 이후 슬랙
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



if __name__ == "__main__":
    file_path = r"C:\Users\user\Desktop\devel\WHS\FineVu_X3000NEW_H265_AVI\FineVu_X3000NEW_H265_AVI\샘플\20250410-13h56m01s_N.avi"
    ext = file_path.split('.')[-1].lower()

    print("[슬랙 정보 분석 결과]")
    
    if ext == "avi":
        result = analyze_avi_slack(file_path)
    elif ext == "mp4":
        result = analyze_mp4_slack(file_path)
    else:
        print("지원하지 않는 파일 형식입니다.")
        exit()

    print(f"전체 크기: {result['total_bytes']} bytes")
    print(f"사용된 크기: {result['valid_data_bytes']} bytes")
    print(f"슬랙 크기: {result['slack_bytes']} bytes")
    print(f"슬랙 비율: {result['slack_ratio_percent']}%")
    print(f"슬랙 영역 개수: {len(result['slack_regions'])}")