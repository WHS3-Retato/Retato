def parse_box(data, offset, file_size, indent_level=0):
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
    output = []  # 출력 저장

    while offset < file_size:  # 파일 끝까지 탐색
        if offset + 8 > file_size:  # 파일 끝 범위 방지
            print(f"[중단] 박스 크기 읽기 실패: offset={hex(offset)}")  # Resolve
            break

        # 박스 크기와 타입 읽기
        try:
            box_size = int.from_bytes(data[offset:offset + 4], byteorder='big')
            box_type = data[offset + 4:offset + 8].decode('utf-8', errors='replace')
        except Exception as e:
            print(f"[오류] 박스 파싱 실패 at offset {hex(offset)}: {e}")  # Resolve
            break

        if box_size < 8 or offset + box_size > file_size:
            print(f"[중단] 비정상적인 박스 크기: {box_type} at offset {hex(offset)} size={box_size}")  # Resolve
            break

        # 박스 정보 추가
        output.append(f"{'    ' * indent_level}{box_type} box start offset: {hex(offset)}")
        output.append(f"{'    ' * indent_level}{box_type} box size: {hex(box_size)}")

        # 하위 박스가 있으면 재귀적으로 파싱
        if box_type in box_hierarchy:
            sub_box_output = parse_box(data, offset + 8, offset + box_size, indent_level + 1)
            output.extend(sub_box_output)

        offset += box_size

    return output

def mp4_parser(file_path):
    with open(file_path, "rb") as file:
        data = file.read()

    file_size = len(data)
    output_lines = parse_box(data, 0, file_size)
    print("\n".join(output_lines))

def avi_parser(file_path):
    with open(file_path, 'rb') as file:
        binary_data = file.read()
        file_size = int.from_bytes(binary_data[4:8], 'little')
        print(f"file size : 0x{file_size:06X}")
        print(f"file data size : 0x{file_size + 8:06X}\n")

        offset = 12
        while offset < len(binary_data):
            chunk_id = binary_data[offset:offset + 4]
            if len(chunk_id) < 4:
                break

            try:
                chunk_size = int.from_bytes(binary_data[offset + 4:offset + 8], "little")
            except Exception as e:
                print(f"[오류] 청크 크기 파싱 실패 at offset {hex(offset)}: {e}")  # Resolve
                break

            chunk_end = offset + 8 + chunk_size
            if chunk_end > len(binary_data):
                print(f"[중단] 청크 크기 초과: {chunk_id.decode(errors='replace')} at offset {hex(offset)} size={chunk_size}")  # Resolve
                break

            if chunk_id == b'stsd':
                stsd_data = binary_data[offset + 8: offset + 8 + chunk_size]
                print(f"stsd Start Offset : 0x{offset:X}")
                print(f"stsd Size : 0x{chunk_size:X}")
                codec_type = stsd_data[10:14].decode('ascii', errors='replace')
                print(f"Codec : {codec_type}")
                codec_data = stsd_data[14:]
                print("Codec Data (Binary):")
                print(codec_data.hex())

            if chunk_id == b'LIST':
                list_subtype = binary_data[offset + 8:offset + 12]
                if list_subtype == b'hdrl':
                    print(f"[LIST-hdrl] offset: 0x{offset:X} size: 0x{chunk_size:X}")
                elif list_subtype == b'movi':
                    print(f"[LIST-movi] offset: 0x{offset:X} size: 0x{chunk_size:X}")
                elif list_subtype == b'INFO':
                    print(f"[LIST-INFO] offset: 0x{offset:X} size: 0x{chunk_size:X}")

            elif chunk_id in [b'JUNK', b'idx1']:
                print(f"{chunk_id.decode(errors='replace')} start offset : 0x{offset:X}")
                print(f"{chunk_id.decode(errors='replace')} size : 0x{chunk_size:X}\n")

            offset += 8 + chunk_size
            if chunk_size % 2 == 1:
                offset += 1

            if offset >= len(binary_data):
                break
