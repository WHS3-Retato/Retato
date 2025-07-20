import os
import json
import shutil
from pathlib import Path
from python_engine.core.image_loader.e01_parser import (
    extract_videos_from_e01,
    VIDEO_EXTENSIONS
)
from python_engine.core.output.download_frame import download_frames

def main():
    # 1) 추출 & 복원
    results, output_dir, total_files = extract_videos_from_e01()
    if total_files == 0 or not results:
        print("추출된 영상이 없습니다. 종료합니다.")
        return

    # 1.1) 분석 결과 JSON 저장 (temp)
    os.makedirs(output_dir, exist_ok=True)
    tmp_json = os.path.join(output_dir, "analysis.json")
    with open(tmp_json, "w", encoding="utf-8") as wf:
        json.dump(results, wf, ensure_ascii=False, indent=2)
    print(f"▶ Temp JSON: {tmp_json}")

    # 1.2) 확인용 sample_video 폴더에도 저장
    sample_dir = os.path.join(os.path.dirname(__file__), "sample_video")
    os.makedirs(sample_dir, exist_ok=True)
    sample_json = os.path.join(sample_dir, "analysis.json")
    with open(sample_json, "w", encoding="utf-8") as wf:
        json.dump(results, wf, ensure_ascii=False, indent=2)
    print(f"▶ Sample JSON: {sample_json}")

    # 2) 저장 항목만 묻기
    print("저장할 항목을 선택하세요:")
    print("1) 영상")
    print("2) 프레임")
    print("3) 둘 다")
    choice = input("선택 (1-3): ").strip()

    # 3) 소스 루트 정의
    # 실제 복원 결과는 output_dir/{category}/… 와 output_dir/{category}/slack 에 모여 있음
    recovery_root = output_dir

    # 4) DOWNLOAD_DIR 준비
    DOWNLOAD_DIR = os.path.join(Path.home(), "Downloads")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # 5) 영상 복사
    if choice in ("1", "3"):
        print("\nRecovery 및 Recovery_Hidden 구조 유지하며 복사 시작...")

        # 5-1) recovery: 원본·전체 채널(.mp4, .avi)
        for root, _, files in os.walk(recovery_root):
            for f in files:
                if f.lower().endswith(VIDEO_EXTENSIONS):
                    src = os.path.join(root, f)
                    rel = os.path.relpath(src, recovery_root)
                    dst = os.path.join(DOWNLOAD_DIR, "recovery", rel)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)

        # 5-2) recovery_hidden: 슬랙 히든 MP4 (output_dir/{category}/slack)
        for category in os.listdir(recovery_root):
            cat_dir = os.path.join(recovery_root, category)
            if not os.path.isdir(cat_dir):
                continue

            slack_dir = os.path.join(cat_dir, "slack")
            if not os.path.isdir(slack_dir):
                continue

            for root, _, files in os.walk(slack_dir):
                for fn in files:
                    if fn.lower().endswith(".mp4"):
                        src = os.path.join(root, fn)
                        rel = os.path.relpath(src, recovery_root)
                        dst = os.path.join(DOWNLOAD_DIR, "recovery_hidden", rel)
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copy2(src, dst)

        print("영상 저장 완료.")

    # 6) 프레임 ZIP으로 저장
    if choice in ("2", "3"):
        # 프레임 추출할 영상 목록 재구성
        videos = []

        # recovery_root 영상
        for root, _, files in os.walk(recovery_root):
            for f in files:
                if f.lower().endswith(VIDEO_EXTENSIONS):
                    videos.append(os.path.join(root, f))

        # recovery_hidden MP4 슬랙
        for category in os.listdir(recovery_root):
            cat_dir = os.path.join(recovery_root, category)
            slack_dir = os.path.join(cat_dir, "slack")
            if not os.path.isdir(slack_dir):
                continue
            for root, _, files in os.walk(slack_dir):
                for f in files:
                    if f.lower().endswith(".mp4"):
                        videos.append(os.path.join(root, f))

        print(f"\n{len(videos)}개 영상의 프레임을 ZIP으로 저장합니다...")
        items = [{"output_path": p, "filename": os.path.basename(p)} for p in videos]
        download_frames(items, download_dir=DOWNLOAD_DIR)
        print("프레임 저장 완료.")

    # 7) 마무리
    print(f"\n모두 '{DOWNLOAD_DIR}'에 저장되었습니다.")
    shutil.rmtree(output_dir, ignore_errors=True)


if __name__ == "__main__":
    main()