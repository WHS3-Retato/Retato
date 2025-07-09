import os
import zipfile
import subprocess
from datetime import datetime
from pathlib import Path
import tempfile

SAMPLE_VIDEO_DIR = r"E:\Retato\python_engine\sample_video"
OUTPUT_VIDEO_DIR = r"E:\Retato\python_engine\sample_output\output_video"
DOWNLOAD_DIR = os.path.join(Path.home(), "Downloads")
FRAME_EXTRACTOR = os.path.abspath("bin/ffmpeg.exe")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def list_videos():
    videos = []
    for directory in [SAMPLE_VIDEO_DIR, OUTPUT_VIDEO_DIR]:
        for file in os.listdir(directory):
            if file.lower().endswith(('.mp4', '.avi')):
                videos.append(os.path.join(directory, file))
    return videos

def classify_zip_name(filename):
    name = os.path.basename(filename)
    stem, ext = os.path.splitext(name)
    ext = ext.lower()

    is_slack = 'slack' in stem.lower()
    is_front = 'front' in stem.lower()
    is_rear = 'rear' in stem.lower()

    timestamp = datetime.fromtimestamp(os.path.getmtime(filename)).strftime('%Y%m%d_%H%M%S')

    label = "_HIDDEN" if is_slack else ""
    if is_front:
        stem = f"{timestamp}_FRONT{label}"
    elif is_rear:
        stem = f"{timestamp}_REAR{label}"
    elif SAMPLE_VIDEO_DIR in filename:
        stem = stem  # 원본 파일은 이름 그대로
    else:
        stem = f"{timestamp}{label}"

    return f"{stem}.zip"

def extract_frames_with_ffmpeg(video_path, output_dir):
    cmd = [
        FRAME_EXTRACTOR,
        "-i", video_path,
        "-q:v", "2",
        os.path.join(output_dir, "frame_%03d.jpg")
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False
    
def zip_directory(source_dir, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)

def zip_frames_from_selected_videos():
    videos = list_videos()
    if not videos:
        print("[INFO] 압축 가능한 영상 파일이 없습니다.")
        return
    
    print("\n[영상 목록]")
    for idx, video in enumerate(videos):
        print(f"{idx + 1}. {os.path.basename(video)}")

    selected = input("\n프레임을 추출하여 압축할 영상 번호를 쉼표(,)로 구분하여 입력하세요 (예: 1,3): ")
    selected_indexes = [int(x.strip()) - 1 for x in selected.split(',') if x.strip().isdigit()]

    if not selected_indexes:
        print("[ERROR] 유효한 선택이 없습니다.")
        return
    
    for idx in selected_indexes:
        try:
            video_path = videos[idx]
            zip_name = classify_zip_name(video_path)
            zip_base, zip_ext = os.path.splitext(zip_name)
            zip_path = os.path.join(DOWNLOAD_DIR, zip_name)

            counter = 1
            while os.path.exists(zip_path):
                zip_name = f"{zip_base}_copy{counter}{zip_ext}"
                zip_path = os.path.join(DOWNLOAD_DIR, zip_name)
                counter += 1

            with tempfile.TemporaryDirectory() as temp_dir:
                print(f"[INFO] 프레임 추출 중: {os.path.basename(video_path)}...")
                success = extract_frames_with_ffmpeg(video_path, temp_dir)
                if not success:
                    print(f"[ERROR] {os.path.basename(video_path)} 프레임 추출 실패")
                    continue

                zip_directory(temp_dir, zip_path)
                print(f"[SUCCESS] {zip_name} 저장 완료 → {DOWNLOAD_DIR}")

        except Exception as e:
            print(f"[ERROR] {os.path.basename(videos[idx])} 처리 실패: {e}")
        
if __name__ == "__main__":
    zip_frames_from_selected_videos()