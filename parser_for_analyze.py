import os
import datetime
import struct

def get_file_format(file_path):
    with open(file_path, 'rb') as f:
        header = f.read(12)

    # AVI: RIFF 헤더
    if header[0:4] == b'RIFF' and header[8:12] == b'AVI ':
        return 'AVI'

    # MP4: ftyp 
    if header[4:8] == b'ftyp':
        return 'MP4'

    return 'Unknown'

def get_file_creation_time(filepath):
    # 생성 시간 (Windows는 실제 생성 시간, UNIX는 최종 변경 시간일 수도 있음)
    timestamp = os.path.getctime(filepath)
    # 사람이 읽을 수 있는 형식으로 변환
    creation_time = datetime.datetime.fromtimestamp(timestamp)
    return creation_time

def mp4_parser(file_path):
    # MP4 박스 계층 구조 정의
    box_hierarchy = {
        "moov": ["mvhd", "trak", "udta", "mvex"],  # moov 내부 박스들
        "trak": ["tkhd", "edts", "mdia"],         # trak 내부 박스들
        "mdia": ["mdhd", "hdlr", "minf"],         # mdia 내부 박스들
        "minf": ["vmhd", "smhd", "dinf", "stbl"], # minf 내부 박스들
        "stbl": ["stsd", "stts", "ctts", "stsc", "stsz", "stz2", "stco", "co64", "stss", "sbgp", "sgpd"],  # 샘플 관련
        "dinf": ["dref"],                         # dinf 내부 박스
        "meta": ["hdlr", "ilst"],                 # meta 관련 박스
        "ilst": ["©nam", "©alb", "©art"],         # 사용자 정의 데이터
    }

    # MP4 박스 파싱 함수
    def parse_box(data, offset, file_size, indent_level=0):
        output = []  # 출력 저장

        while offset < file_size:  # 파일 끝까지 탐색
            if offset + 8 > file_size:  # 파일 끝 범위 방지
                break

            # 박스 크기와 타입 읽기
            box_size = int.from_bytes(data[offset:offset + 4], byteorder='big')  # 박스 크기 (빅 엔디안)
            box_type = data[offset + 4:offset + 8].decode('utf-8', errors='replace')  # 박스 타입 디코딩

            if box_size < 8 or offset + box_size > file_size:  # 잘못된 박스 크기 처리
                break

            # 박스 정보 추가
            output.append(f"{'    ' * indent_level}{box_type} box start offset: {hex(offset)}")  # 박스 시작 위치
            output.append(f"{'    ' * indent_level}{box_type} box size: {hex(box_size)}")  # 박스 크기

            # 하위 박스가 있으면 재귀적으로 파싱
            if box_type in box_hierarchy:  # 계층 구조에 정의된 박스만
                sub_box_output = parse_box(data, offset + 8, offset + box_size, indent_level + 1)  # 내부 탐색
                output.extend(sub_box_output)

            offset += box_size  # offset 이동

        return output  # 결과 반환

    # 파일 열기 및 데이터 읽기
    with open(file_path, "rb") as file:
        data = file.read()

    file_size = len(data)  # 파일 크기 계산
    output_lines = parse_box(data, 0, file_size)  # MP4 파싱 실행
    print("\n".join(output_lines))  # 결과 출력

def avi_parser(file_path):
    with open(file_path, 'rb') as file:
    # 전체 파일 크기 확인
        binary_data = file.read()
        file_size = int.from_bytes(binary_data[4:8], 'little')  # RIFF 크기 추출
        print(f"file size : 0x{file_size:06X}")
        print(f"file data size : 0x{file_size + 8:06X}\n")  # RIFF + 8바이트 헤더 포함 크기

        # 파일 처음으로 이동
        offset = 12  # RIFF 헤더를 건너뛴 위치
        while offset < len(binary_data):  # 전체 파일 끝까지 탐색
            # 청크 ID 및 크기 추출
            chunk_id = binary_data[offset:offset+4]
            if len(chunk_id) < 4:  # ID를 읽을 수 없으면 종료
                break
            chunk_size = int.from_bytes(binary_data[offset+4:offset+8], "little")

            # `stsd` 청크 파싱
            if chunk_id == b'stsd':
                stsd_data = binary_data[offset + 8: offset + 8 + chunk_size]
                print(f"stsd Start Offset : 0x{offset:X}")
                print(f"stsd Size : 0x{chunk_size:X}")
                
                # 코덱 정보 추출
                codec_type = stsd_data[10:14].decode('ascii', errors='replace')  # 10번째 바이트부터 4바이트(FourCC 코드)
                print(f"Codec : {codec_type}")
                
                # 코덱 데이터 추출
                codec_data = stsd_data[14:]  # 14번째 바이트부터 끝까지 (코덱 초기화 데이터)
                print("Codec Data (Binary):")
                print(codec_data.hex())  # 바이너리 데이터를 헥사로 출력




            # LIST 청크 처리
            if chunk_id == b'LIST':
                list_subtype = binary_data[offset+8:offset+12]
                if list_subtype == b'hdrl':
                    print(f"[LIST-hdrl] offset: 0x{offset:X} size: 0x{chunk_size:X}")
                elif list_subtype == b'movi':
                    print(f"[LIST-movi] offset: 0x{offset:X} size: 0x{chunk_size:X}")
                elif list_subtype == b'INFO':
                    print(f"[LIST-INFO] offset: 0x{offset:X} size: 0x{chunk_size:X}")


            # 기타 청크 처리
            elif chunk_id in [b'JUNK', b'idx1']:
                print(f"{chunk_id.decode(errors='replace')} start offset : 0x{offset:X}")
                print(f"{chunk_id.decode(errors='replace')} size : 0x{chunk_size:X}\n")

            # offset 이동
            offset += 8 + chunk_size  # ID(4바이트) + 크기(4바이트) + 데이터 크기
            if chunk_size % 2 == 1:  # 짝수 정렬 처리 (패딩 바이트 스킵)
                offset += 1

            # 파일 끝 범위 초과 방지
            if offset >= len(binary_data):
                break

def avi_damage_check(file_path):
    reasons = []
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        print("True")
        print(f"파일 열기 실패: {e}")
        return

    # 1. RIFF 헤더 확인
    if not data.startswith(b'RIFF'):
        print("True")
        print("[헤더 손상] 파일이 'RIFF' 시그니처로 시작하지 않습니다.")
        return

    # 2. 파일 크기 불일치
    riff_size = struct.unpack('<I', data[4:8])[0] + 8
    actual_size = len(data)
    if abs(riff_size - actual_size) > 1024:
        reasons.append(f"[파일 크기 손상] 'RIFF'에 기록된 크기({riff_size})와 실제 크기({actual_size}) 불일치합니다.")

    # 3. movi 청크 확인
    if b'movi' not in data:
        reasons.append("[필수 청크 손상] 'movi' 청크 X → 프레임 누락 가능성이 있습니다.")

    # 4. 프레임 청크 개수 확인
    front_count = data.count(b'00dc')
    rear_count = data.count(b'01dc')
    if front_count == 0 or rear_count == 0:
        reasons.append("[프레임 청크 식별 불가능] '00dc' 또는 '01dc' 프레임 청크 X → 전/후방 데이터가 없을 가능성이 있습니다.")

    # 최종 출력
    if reasons:
        print("True")
        for r in reasons:
            print(r)
    else:
        print("False")

def mp4_damage_check(file_path):
    reasons = []

    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        print("True")
        print(f"파일 열기 실패: {e}")
        return

    def find_box(data, box_type):
        offset = 0
        while offset < len(data) - 8:
            try:
                size = struct.unpack(">I", data[offset:offset+4])[0]
                typ = data[offset+4:offset+8]
                if typ == box_type.encode():
                    return offset, size
                offset += size if size > 0 else 8
            except:
                break
        return None, None

    # 1. ftyp 박스 확인
    ftyp_offset, ftyp_size = find_box(data, 'ftyp')
    if ftyp_offset is None:
        print("True")
        print("[필수 atom 손상] 'ftyp' 박스 없음 → MP4 파일 구조가 아닐 가능성이 있습니다.")
        return
    elif ftyp_offset != 0:
        reasons.append(f"[구조 손상] 'ftyp' 박스가 파일 시작이 아님 (offset: {ftyp_offset}) → 비정상 구조일 수 있음.")

    # 2. moov, mdat 박스 확인
    moov_offset, moov_size = find_box(data, 'moov')
    mdat_offset, mdat_size = find_box(data, 'mdat')

    if moov_offset is None:
        reasons.append("[필수 atom 손상] 'moov' 박스 없음 → 메타데이터 손상 가능성이 있습니다.")
    if mdat_offset is None:
        reasons.append("[필수 atom 손상] 'mdat' 박스 없음 → 실제 영상 데이터가 없을 수 있습니다.")

    # 3. moov, mdat 순서 확인
    if moov_offset is not None and mdat_offset is not None:
        if moov_offset > mdat_offset:
            reasons.append("'moov' 박스가 'mdat' 뒤에 위치 → 일부 재생기에서 오류 발생할 수 있음.")

    # 최종 출력
    if reasons:
        print("True")
        for r in reasons:
            print(r)
    else:
        print("False")

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