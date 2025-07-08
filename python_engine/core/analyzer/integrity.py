import struct

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

if __name__ == "__main__":
    file_path = r"C:\\Users\\user\\Desktop\\devel\\WHS\\FineVu_X3000NEW_H265_AVI\\FineVu_X3000NEW_H265_AVI\\샘플\\20250410-13h56m01s_N.avi"

    print("[무결성 검사 결과]")
    file_ext = file_path.split('.')[-1].lower()

    if file_ext == 'avi':
        avi_damage_check(file_path)
    elif file_ext == 'mp4':
        mp4_damage_check(file_path)
    else:
        print("지원되지 않는 파일 형식입니다.")
