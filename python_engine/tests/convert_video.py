import subprocess
import os

# ffmpeg.exe 절대경로 (사용자 환경에 맞게 수정하세요)
FFMPEG_PATH = r"E:\Retato\bin\ffmpeg.exe"

# 입력 H.264 파일과 출력 MP4 파일 경로
H264_PATH = r"E:\Retato\python_engine\sample_output\avi_slack_front.h264"

def run_ffmpeg(h264_path, output_path, codec, fps=30):
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
    
def convert_h264(h264_path, output_path, container_format, fps=30):
    if not os.path.exists(FFMPEG_PATH):
        raise FileNotFoundError(f"FFmpeg 실행 파일을 찾을 수 없습니다: {FFMPEG_PATH}")
    if not os.path.exists(h264_path):
        raise FileNotFoundError(f"입력 파일이 존재하지 않습니다: {h264_path}")
    
    # 기본적으로 copy 시도
    codec = "copy"
    result = run_ffmpeg(h264_path, output_path, codec, fps)

    # avi 컨테이너 + copy 실패 → libx264 재시도
    if result.returncode != 0 and container_format == "avi":
        print("[경고] copy codec으로 avi 컨테이너 변환 실패 → libx264로 재시도")
        codec = "libx264"
        result = run_ffmpeg(h264_path, output_path, codec, fps)
    
    # 결과 출력
    if result.returncode != 0:
        print(f"[오류] FFmpeg 실행 실패:\n{result.stderr}")
    else:
        print(f"[성공] {container_format.upper()} 컨테이너로 변환 완료 → {output_path}")

if __name__ == "__main__":
    format_choice = input("저장할 포맷을 입력하세요 (mp4 또는 avi): ").strip().lower()

    if format_choice not in ('mp4', 'avi'):
        print("지원하지 않는 포맷입니다. 'mp4' 또는 'avi' 중 하나를 입력하세요.")
    else:
        output_path = H264_PATH.replace(".h264", f".{format_choice}")
        convert_h264(H264_PATH, output_path, container_format=format_choice)