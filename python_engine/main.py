import os
import sys
import json
import shutil
from python_engine.core.image_loader.e01_parser import extract_videos_from_e01
from python_engine.core.output.download_frame import download_frames

def main(e01_path, choice=None, download_dir=None):
    # 1) 추출 & 복원
    results, output_dir, total_files = extract_videos_from_e01(e01_path)
    if total_files == 0 or not results:
        # 결과 없음
        print(json.dumps([]), flush=True)
        return

    # 1.1) 분석 결과 JSON 저장 (temp)
    os.makedirs(output_dir, exist_ok=True)
    tmp_json = os.path.join(output_dir, "analysis.json")
    with open(tmp_json, "w", encoding="utf-8") as wf:
        json.dump(results, wf, ensure_ascii=False, indent=2)

    # 디버그 로그는 stderr 로
    print(f"▶ Temp JSON: {tmp_json}", file=sys.stderr, flush=True)

    # 1.2) stdout에는 analysisPath JSON만
    print(json.dumps({"analysisPath": tmp_json}), flush=True)

    # ───────────────────────────────────────────────────────────────────────────
    # 2) 다운로드 모드: choice가 주어졌을 때만 실행
    if choice and download_dir:
        DOWNLOAD_DIR = download_dir
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        # 2.1) 영상 복사/변환
        if choice in ("video", "both"):
            print("▶ 영상 저장 시작...", file=sys.stderr)
            # 전체 채널(.mp4, .avi)
            for root, _, files in os.walk(output_dir):
                for f in files:
                    if f.lower().endswith((".mp4", ".avi")):
                        src = os.path.join(root, f)
                        rel = os.path.relpath(src, output_dir)
                        dst = os.path.join(DOWNLOAD_DIR, "recovery", rel)
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copy2(src, dst)
            # 슬랙 히든 MP4
            for category in os.listdir(output_dir):
                slack_dir = os.path.join(output_dir, category, "slack")
                if os.path.isdir(slack_dir):
                    for root, _, files in os.walk(slack_dir):
                        for fn in files:
                            if fn.lower().endswith(".mp4"):
                                src = os.path.join(root, fn)
                                rel = os.path.relpath(src, output_dir)
                                dst = os.path.join(DOWNLOAD_DIR, "recovery_hidden", rel)
                                os.makedirs(os.path.dirname(dst), exist_ok=True)
                                shutil.copy2(src, dst)
            print("▶ 영상 저장 완료.", file=sys.stderr)

        # 2.2) 프레임 ZIP 생성
        if choice in ("both", "frames"):
            print("▶ 프레임 ZIP 저장 시작...", file=sys.stderr)
            # analysis.json 기반으로 items 구성
            with open(tmp_json, 'r', encoding='utf-8') as rf:
                infos = json.load(rf)
            # download_frames는 {'output_path', 'filename'} 리스트를 받음
            items = [
                {"output_path": info["output_path"], "filename": info["filename"]}
                for info in infos
            ]
            download_frames(items, download_dir=DOWNLOAD_DIR)
            print("▶ 프레임 저장 완료.", file=sys.stderr)

        # 2.3) temp 폴더(analysis.json 포함) 삭제
        shutil.rmtree(output_dir, ignore_errors=True)
        print(f"▶ 모든 파일이 '{DOWNLOAD_DIR}'에 저장되었고, 임시 폴더를 정리했습니다.", file=sys.stderr)

if __name__ == "__main__":
    # Usage:
    # 1) 분석만: python main.py <E01_PATH>
    # 2) 다운로드: python main.py <E01_PATH> <video|frames|both> <DOWNLOAD_DIR>
    if len(sys.argv) == 2:
        main(sys.argv[1])
    elif len(sys.argv) == 4:
        _, e01_path, choice, download_dir = sys.argv
        main(e01_path, choice, download_dir)
    else:
        print("Usage:", file=sys.stderr)
        print("  분석만:  python main.py <E01_PATH>", file=sys.stderr)
        print("  다운로드: python main.py <E01_PATH> <video|frames|both> <DOWNLOAD_DIR>", file=sys.stderr)
        sys.exit(1)