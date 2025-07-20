import os
import shutil
import logging
from python_engine.core.recovery.utils.ffmpeg_wrapper import convert_video

logger = logging.getLogger(__name__)

def download_videos(video_info_list, download_dir, video_format="mp4"):
    os.makedirs(download_dir, exist_ok=True)
    saved = []

    for info in video_info_list:
        input_path = info.get("output_path")
        h264_path = info.get("h264_path")
        original_name = info.get("filename")

        if not input_path or not os.path.exists(input_path):
            logger.warning(f"유효하지 않은 영상: {input_path}")
            continue

        # 슬랙 영상 여부 판단
        is_slack = "slack" in original_name.lower() or "hidden" in original_name.lower()
        desired_fmt = video_format.lower()
        orig_ext = os.path.splitext(input_path)[1].lower().lstrip('.')

        name = os.path.splitext(original_name)[0]
        counter = 1
        out_name = f"{name}.{desired_fmt}"
        output_path = os.path.join(download_dir, out_name)
        while os.path.exists(output_path):
            output_path = os.path.join(download_dir, f"{name}_copy{counter}.{desired_fmt}")
            counter += 1

        try:
            if is_slack and h264_path:
                # 슬랙은 raw h264 -> mp4 고정
                logger.info(f"[SLACK] 변환: {original_name} → {output_path}")
                success = convert_video(h264_path, output_path, "mp4")
                if not success:
                    logger.error(f"슬랙 영상 변환 실패: {original_name}")
                    continue
            
            else:
                # non-slack 또는 슬랙이지만 h264_path 없을 때
                # 1) 원본 확장자 == 원하는 포맷: 그대로 복사
                if orig_ext == desired_fmt:
                    shutil.copy2(input_path, output_path)
                    logger.info(f"복사 완료: {original_name} → {output_path}")
                
                # 2) 확장자가 다르면 FFmpeg로 변환 시도
                else:
                    logger.info(f"변환 시도: {original_name} ({orig_ext} → {desired_fmt})")
                    success = convert_video(input_path, output_path, desired_fmt)
                    if not success:
                        logger.warning(f"변환 실패: {original_name} → {desired_fmt}")
                        # fallback: 만약 avi 변환 실패 시 mp4로 시도
                        if desired_fmt == "avi":
                            fb_path = os.path.splitext(output_path)[0] + ".mp4"
                            fb_success = convert_video(input_path, fb_path, "mp4")
                            if fb_success:
                                output_path = fb_path
                                desired_fmt = "mp4"
                                logger.info(f"fallback mp4 변환 성공 → {fb_path}")
                            else:
                                logger.error(f"fallback mp4 변환도 실패: {original_name}")
                                continue
                        else:
                            continue

            # 최종 파일 체크
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                saved.append({
                    "saved_path": output_path,
                    "filename": os.path.basename(output_path)
                })
            else:
                logger.warning(f"파일이 생성되지 않았거나 0바이트: {output_path}")
                if os.path.exists(output_path):
                    os.remove(output_path)
        
        except Exception as e:
            logger.error(f"다운로드 중 예외 발생 ({original_name}): {e}")
    
    return saved