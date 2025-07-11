import os
import json
import datetime
import struct
import pyewf
import pytsk3
import tkinter as tk
from tkinter import filedialog
from io import BytesIO
import time
import logging
from python_engine.core.recovery.mp4.extract_slack import recover_mp4_slack
from python_engine.core.recovery.avi.extract_slack import recover_avi_slack
from python_engine.core.recovery.avi.avi_split_channel import split_avi_channels

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = ('.mp4', '.avi')
OUTPUT_DIR = os.path.join("python_engine", "sample_output", "extracted_videos")

class EWFImgInfo(pytsk3.Img_Info):
    def __init__(self, ewf_handle):
        self._ewf_handle = ewf_handle
        super().__init__("", pytsk3.TSK_IMG_TYPE_EXTERNAL)

    def read(self, offset, size):
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        return self._ewf_handle.get_media_size()

def open_e01_image(e01_path):
    e01_path = os.path.abspath(e01_path)
    filenames = pyewf.glob(e01_path)
    ewf_handle = pyewf.handle()
    ewf_handle.open(filenames)
    return EWFImgInfo(ewf_handle)

def classify_by_prefix(name):
    return name.lower().split("_")[0]

def has_mp4_slack(data, min_slack_size=1024*1024):
    try:
        offset = 0
        file_size = len(data)
        last_moov_end = 0

        while offset + 8 < file_size:
            size = struct.unpack('>I', data[offset:offset+4])[0]
            box_type = data[offset + 4:offset + 8]

            if size < 8 or offset + size > file_size:
                break

            if box_type == b'moov':
                last_moov_end = offset + size
        
            offset += size

        if last_moov_end > 0:
            slack_size = file_size - last_moov_end
            return slack_size > min_slack_size
    except:
        return False
    return False

def has_avi_slack(data, min_slack_size=1024*1024):
    try:
        if data[:4] != b'RIFF':
            return False
        
        file_size = len(data)
        riff_size = struct.unpack('<I', data[4:8])[0]
        riff_end = 8 + riff_size

        cursor = 12
        last_chunk_end = cursor
        slack_regions = []

        while cursor + 8 <= file_size:
            chunk_start = cursor

            try:
                chunk_size = struct.unpack('<I', data[cursor + 4:cursor + 8])[0]
            except:
                break

            chunk_end = cursor + 8 + chunk_size
            if chunk_end > file_size:
                break

            if chunk_start > last_chunk_end:
                slack_regions.append((last_chunk_end, chunk_start))

            last_chunk_end = chunk_end
            cursor = chunk_end

            if chunk_size % 2 == 1:
                cursor += 1
                last_chunk_end += 1
        
        # RIFF 끝 이후 슬랙
        if riff_end < file_size:
            slack_regions.append((riff_end, file_size))

        slack_size = sum(end - start for start, end in slack_regions)
        return slack_size > min_slack_size
    except:
        return False

def count_video_files(fs_info, path="/"):
    count = 0
    try:
        directory = fs_info.open_dir(path=path)
        for entry in directory:
            if entry.info.name.name in [b'.', b'..'] or entry.info.meta is None:
                continue

            name = entry.info.name.name.decode('utf-8', 'ignore')
            filepath = f"{path.rstrip('/')}/{name}"

            if entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
                count += count_video_files(fs_info, filepath)
            elif name.lower().endswith(VIDEO_EXTENSIONS):
                count += 1
    except Exception as e:
        logger.warning(f"파일 수 세기 실패: {path} → {e}")
    return count

def extract_video_files(fs_info, output_dir, path="/", include_all=True, total_count=None, progress=None):
    results = []
    created_dirs = set()
    directory = fs_info.open_dir(path=path)

    for entry in directory:
        if entry.info.name.name in [b'.', b'..'] or entry.info.meta is None:
            continue

        name = entry.info.name.name.decode('utf-8', 'ignore')
        name_lower = name.lower()
        filepath = f"{path.rstrip('/')}/{name}"

        if entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
            results.extend(extract_video_files(fs_info, output_dir, filepath, include_all, total_count, progress))
            continue

        if not name.lower().endswith(VIDEO_EXTENSIONS):
            continue

        try:
            if progress is not None:
                progress[0] += 1
                print(f"[{progress[0]}/{total_count}] 처리 중: {filepath}")

            f = fs_info.open(filepath)
            size = f.info.meta.size
            ctime = f.info.meta.crtime
            ctime_str = datetime.datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M:%S") if ctime else None

            # 메모리 상에서 영상 데이터 읽기
            buffer = BytesIO()
            offset = 0
            max_iterations = size // (4 * 1024 * 1024) + 20

            iteration = 0
            while offset < size and iteration < max_iterations:
                chunk_size = min(4 * 1024 * 1024, size - offset)
                chunk = f.read_random(offset, chunk_size)
                
                if not chunk:
                    logger.warning(f"{filepath} → chunk가 비어 있음. 루프 중단.")
                    break

                buffer.write(chunk)
                offset += len(chunk)
                iteration += 1
            
            if iteration >= max_iterations:
                logger.warning(f"{filepath} → max_iterations 도달. 루프 강제 종료.")

            full_data = buffer.getvalue()
            suspected_slack = False
            
            if name_lower.endswith(".mp4"):
                suspected_slack = has_mp4_slack(full_data)
            elif name_lower.endswith(".avi"):
                suspected_slack = has_avi_slack(full_data)

            if not include_all and not suspected_slack:
                logger.info(f"[SKIP] {filepath} → 슬랙 의심 영역 없음")
                continue

            category = classify_by_prefix(name)
            category_dir = os.path.join(output_dir, category)

            if category_dir not in created_dirs:
                os.makedirs(category_dir, exist_ok=True)
                created_dirs.add(category_dir)

            final_path = os.path.join(category_dir, name)

            with open(final_path, 'wb') as out_file:
                out_file.write(full_data)

            print(f"[SAVED] 추출 완료: {final_path}")

            # 복원 정보 초기값
            slack_info = {}
            split_info = {}

            if name_lower.endswith(".mp4"):
                recovery = recover_mp4_slack(
                    filepath=final_path,
                    output_h264_dir=os.path.join(output_dir, "recovered_h264"),
                    output_video_dir=os.path.join(output_dir, "recovered_mp4")
                )
                slack_info.update({
                    "recovered_slack": recovery["recovered"],
                    "recovered_slack_frame_count": recovery["frame_count"],
                    "recovered_slack_path": recovery["output_path"]
                })
            
            elif name_lower.endswith(".avi"):
                recovery = recover_avi_slack(
                    filepath=final_path,
                    output_h264_dir=os.path.join(output_dir, "recovered_h264"),
                    output_video_dir=os.path.join(output_dir, "recovered_mp4")
                )
                slack_info.update({
                    "avi_front": recovery["front"],
                    "avi_rear": recovery["rear"]
                })

                split = split_avi_channels(
                    filepath=final_path,
                    output_h264_dir=os.path.join(output_dir, "split_h264"),
                    output_video_dir=os.path.join(output_dir, "split_mp4")
                )
                split_info["avi_channel_split"] = {
                    "front": split["front"],
                    "rear": split["rear"]
                }

            # 결과 기록
            results.append({
                "name": name,
                "category": category,
                "path": filepath,
                "size": size,
                "ctime": ctime_str,
                "saved_path": final_path,
                "suspected_slack": suspected_slack,
                "slack_info": slack_info,
                "split_info": split_info
            })

        except Exception as e:
            logger.error(f"{filepath} 추출 실패: {e}")

    return results

def select_e01_file():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilename(title="E01 파일 선택", filetypes=[("E01 파일", "*.E01")])

def ask_extraction_mode():
    print("\n[SELECT] 어떤 영상만 추출할까요?")
    print("1. 전체 영상")
    print("2. 슬랙 영상이 포함된 영상만 추출")
    return input("선택 (1 또는 2): ").strip() == "1"

def main():
    start_time = time.time()

    print("[INFO] E01 이미지 파일을 선택해주세요.")
    e01_path = select_e01_file()

    if not e01_path:
        print("[ERROR] E01 파일을 선택하지 않았습니다. 종료합니다.")
        return

    include_all = ask_extraction_mode()
    logger.info(f"선택 모드: {'전체 추출' if include_all else '슬랙 영상만 추출'}")
    if include_all:
        print("[WARNING] 전체 추출은 시간이 오래 걸릴 수 있습니다. 잠시만 기다려 주세요 ...")
    
    try:
        img_info = open_e01_image(e01_path)
        volume = pytsk3.Volume_Info(img_info)
    except Exception as e:
        logger.error(f"E01 이미지 열기 실패: {e}")
        return
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for part in volume:
        try:
            fs_offset = part.start * 512
            fs_info = pytsk3.FS_Info(img_info, offset=fs_offset)

            logger.info("전체 영상 수를 계산 중입니다...")
            total_files = count_video_files(fs_info)
            logger.info(f"총 대상 영상 수: {total_files}개")

            progress = [0]

            results = extract_video_files(
                fs_info,
                OUTPUT_DIR,
                include_all=include_all,
                total_count=total_files,
                progress=progress
            )

            # 결과를 JSON으로 저장
            if results:
                with open(os.path.join(OUTPUT_DIR, "extracted_videos.json"), "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"총 {total_files}개 중 {len(results)}개의 영상이 추출되었습니다.")
            else:
                print(f"추출된 영상이 없습니다.")
            break
        except Exception as e:
            logger.error(f"파티션 열기 실패: {e}")
    else:
        logger.error("분석 가능한 파티션을 찾을 수 없습니다.")

    elapsed = int(time.time() - start_time)
    logger.info(f"총 소요 시간: {elapsed // 3600}시간 {(elapsed % 3600) // 60}분 {elapsed % 60}초")

if __name__ == "__main__":
    main()