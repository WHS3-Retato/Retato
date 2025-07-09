import os
import shutil
from datetime import datetime
from pathlib import Path

SAMPLE_VIDEO_DIR = r"E:\Retato\python_engine\sample_video"
OUTPUT_VIDEO_DIR = r"E:\Retato\python_engine\sample_output\output_video"
DOWNLOAD_DIR = os.path.join(Path.home(), "Downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def list_videos():
    videos = []
    for directory in [SAMPLE_VIDEO_DIR, OUTPUT_VIDEO_DIR]:
        for file in os.listdir(directory):
            if file.lower().endswith(('.mp4', '.avi')):
                videos.append(os.path.join(directory, file))
    return videos

def classifty_video_name(filename):
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

    return stem
    
def download_selected_videos():
    videos = list_videos()
    if not videos:
        print("[INFO] 복원된 영상이 존재하지 않습니다.")
        return
    
    print("\n[영상 목록]")
    for idx, video in enumerate(videos):
        print(f"{idx + 1}. {os.path.basename(video)}")

    selected = input("\n다운로드할 영상 번호를 쉼표(,)로 구분하여 입력하세요 (예: 1,3,4):" )
    selected_indexes = [int(x.strip()) - 1 for x in selected.split(',') if x.strip().isdigit()]

    if not selected_indexes:
        print("[ERROR] 유효한 선택이 없습니다.")
        return
    
    format_input = input("다운로드 포맷을 선택하세요 (mp4 또는 avi): ").strip().lower()
    if format_input not in ["mp4", "avi"]:
        print("[ERROR] 지원되지 않는 포맷입니다.")
        return
    
    for idx in selected_indexes:
        try:
            src = videos[idx]
            dst_stem = classifty_video_name(src)
            dst_filename = f"{dst_stem}.{format_input}"
            dst_path = os.path.join(DOWNLOAD_DIR, dst_filename)

            # 이미 같은 이름이 있다면 _copy 붙여서 저장
            counter = 1
            while os.path.exists(dst_path):
                dst_filename = f"{dst_stem}_copy{counter}.{format_input}"
                dst_path = os.path.join(DOWNLOAD_DIR, dst_filename)
                counter += 1

            shutil.copy2(src, dst_path)
            print(f"[SUCCESS] {dst_filename} 다운로드 완료 → {DOWNLOAD_DIR}")
        except Exception as e:
            print(f"[ERROR] {os.path.basename(src)} 다운로드 실패: {e}")

if __name__ == "__main__":
    download_selected_videos()