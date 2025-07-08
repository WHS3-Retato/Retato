import os
import datetime
import subprocess
import json
from fractions import Fraction

def file_format(file_path):
    with open(file_path, 'rb') as f:
        header = f.read(12)

    # AVI: RIFF 헤더
    if header[0:4] == b'RIFF' and header[8:12] == b'AVI ':
        return 'AVI'

    # MP4: ftyp 
    if header[4:8] == b'ftyp':
        return 'MP4'

    return 'Unknown'

def file_creation_time(file_path):
    created_timestamp = os.path.getctime(file_path)
    modified_timestamp = os.path.getmtime(file_path)
    access_timestamp = os.path.getatime(file_path)

    # 사람이 읽을 수 있는 형태로 변환
    creation_time = datetime.datetime.fromtimestamp(created_timestamp)
    modified_time = datetime.datetime.fromtimestamp(modified_timestamp)
    access_time = datetime.datetime.fromtimestamp(access_timestamp)
    
    return creation_time, modified_time, access_time

def video_metadata(file_path):
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name,width,height,r_frame_rate,duration',
        '-of', 'json',
        file_path
    ]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        info = json.loads(result.stdout)

        streams = info.get('streams', [])  # Resolve: KeyError 방지
        if not streams:
            raise ValueError("스트림 정보가 없습니다.")  # Resolve: IndexError 방지

        stream = streams[0]
        codec = stream.get('codec_name', 'unknown')
        width = int(stream.get('width', 0))
        height = int(stream.get('height', 0))
        duration = float(stream.get('duration', 0.0))

        fps_str = stream.get('r_frame_rate', '0/1')
        try:
            frame_rate = float(Fraction(fps_str))  # Resolve: eval() 제거 → 안전한 방식으로 대체
        except:
            frame_rate = 0.0

        return {
            'duration': duration,
            'codec': codec,
            'width': width,
            'height': height,
            'frame_rate': frame_rate
        }

    except Exception as e:
        print(f"[오류] 메타데이터 추출 실패: {e}")
        return {
            'duration': 0.0,
            'codec': 'unknown',
            'width': 0,
            'height': 0,
            'frame_rate': 0.0
        }

def file_size(file_path):
    # 파일 크기 (bytes 단위) 반환
    return os.path.getsize(file_path)
