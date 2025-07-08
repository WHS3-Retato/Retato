import subprocess
import os

# FFmpeg 경로
FFMPEG_PATH = r"E:\Retato\bin\ffmpeg.exe"

def run_ffmpeg(h264_path, output_path, codec, fps=30, ffmpeg_path=FFMPEG_PATH):
    cmd = [
        FFMPEG_PATH, "-y",
        "-f", "h264",
        "-r", str(fps),
        "-i", h264_path,
        "-c:v", codec,
        output_path
    ]
    print(f"[FFmpeg] 실행 중: {' '.join(cmd)}")
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def convert_video(h264_path, output_path, container_format, fps=30, ffmpeg_path=FFMPEG_PATH):
    # 유효성 검사
    if not os.path.exists(FFMPEG_PATH):
        raise FileNotFoundError(f"FFmpeg 실행 파일을 찾을 수 없습니다: {FFMPEG_PATH}")
    if not os.path.exists(h264_path):
        raise FileNotFoundError(f"입력 파일이 존재하지 않습니다: {h264_path}")
    
    # 기본적으로 copy 시도
    codec = "copy"
    result = run_ffmpeg(h264_path, output_path, codec, fps, ffmpeg_path)

    # avi 실패 시 fallback: libx264
    if result.returncode != 0 and container_format == "avi":
        print("[경고] copy codec으로 avi 컨테이너 변환 실패 → libx264로 재시도")
        codec = "libx264"
        result = run_ffmpeg(h264_path, output_path, codec, fps, ffmpeg_path)
    
    # 결과 출력
    if result.returncode != 0:
        print(f"[오류] FFmpeg 실행 실패:\n{result.stderr}")
        return False
    
    print(f"[성공] {container_format.upper()} 컨테이너로 변환 완료 → {output_path}")
    return True