import os
import zipfile
import subprocess
import tempfile
import logging

logger = logging.getLogger(__name__)
FRAME_EXTRACTOR = os.path.abspath("bin/ffmpeg.exe")

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

def download_frames(video_info_list, download_dir):
    os.makedirs(download_dir, exist_ok=True)
    saved = []

    for info in video_info_list:
        video_path = info.get("output_path")
        filename = info.get("filename")

        if not video_path or not filename or not os.path.exists(video_path):
            logger.warning(f"유효하지 않은 영상: {video_path}")
            continue

        name, _ = os.path.splitext(filename)
        zip_name = f"{name}.zip"
        zip_path = os.path.join(download_dir, zip_name)

        counter = 1
        while os.path.exists(zip_path):
            zip_path = os.path.join(download_dir, f"{name}_copy{counter}.zip")
            counter += 1

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                logger.info(f"프레임 추출 중: {filename}")
                success = extract_frames_with_ffmpeg(video_path, temp_dir)
                if not success:
                    logger.error(f"프레임 추출 실패: {filename}")
                    continue

                zip_directory(temp_dir, zip_path)
                logger.info(f"압축 완료: {zip_path}")
                saved.append({ "saved_path": zip_path, "filename": os.path.basename(zip_path) })

        except Exception as e:
            logger.error(f"{filename} 처리 중 예외 발생 {e}")

    
    return saved