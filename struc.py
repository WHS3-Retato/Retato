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

if __name__ == "__main__":
    file_path = r"C:\Users\user\Desktop\devel\WHS\INAVI_QXD1500_H264_MP4\INAVI_QXD1500_H264_MP4\샘플\MOT_2025_04_13_18_00_32_F.MP4"
    ext = file_path.split('.')[-1].lower()

    print("[파일 구조 파싱 결과]\n")
    
    if ext == "mp4":
        mp4_parser(file_path)
    elif ext == "avi":
        avi_parser(file_path)
    else:
        print("지원하지 않는 형식입니다.")
