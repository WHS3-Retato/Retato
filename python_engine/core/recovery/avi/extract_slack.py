import os
import struct
import logging
from python_engine.core.recovery.utils.ffmpeg_wrapper import convert_video

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

MAX_REASONABLE_CHUNK_SIZE = 10 * 1024 * 1024
FRONT_SIGNATURE = b'00dc'
REAR_SIGNATURE = b'01dc'

def extract_channel_from_slack(data, start_offset, signature):
    offset = start_offset
    end = len(data)
    chunks = []
    sps = pps = None
    count = 0

    while offset < end - 8:
        index = data.find(signature, offset, end)
        if index == -1 or index + 8 > end:
            break

        try:
            size = struct.unpack('<I', data[index + 4: index + 8])[0]
        except:
            offset = index + 1
            continue

        chunk_start = index + 8
        chunk_end = chunk_start + size
        aligned = size + (size % 2)

        # 프레임 크기 유효성 검사
        if size > MAX_REASONABLE_CHUNK_SIZE:
            logger.debug(f"비정상적으로 큰 프레임 (size={size}, offset=0x{index:X}) → skip")
            offset = index + 4
            continue
        if size < 5:
            logger.debug(f"너무 작은 프레임 (size={size}, offset=0x{index:X}) → skip")
            offset = index + 4
            continue
        if chunk_end > end:
            logger.debug(f"프레임이 파일 끝을 넘어감 (size={size}, offset=0x{index:X}) → skip")
            offset = index + 4
            continue

        # NAL 검사
        if data[chunk_start:chunk_start + 4] != b'\x00\x00\x00\x01':
            logger.debug(f"잘못된 NAL prefix (offset=0x{index:X}) → skip")
            offset = index + 4
            continue

        nal_type = data[chunk_start + 4] & 0x1F
        frame = data[chunk_start:chunk_end]

        if nal_type == 7 and sps is None:
            sps = frame
        elif nal_type == 8 and pps is None:
            pps = frame

        if nal_type in (1, 5, 7, 8):
            chunks.append(frame)
            count += 1

        offset = index + 8 + aligned

    return chunks, count, sps, pps

def write_chunks(filepath, chunks, sps=None, pps=None):
    with open(filepath, 'wb') as f:
        if sps and pps:
            f.write(sps)
            f.write(pps)
        for chunk in chunks:
            f.write(chunk)

def recover_avi_slack(filepath, output_h264_dir, output_video_dir, target_format="mp4"):
    os.makedirs(output_h264_dir, exist_ok=True)
    os.makedirs(output_video_dir, exist_ok=True)

    filename = os.path.splitext(os.path.basename(filepath))[0]
    with open(filepath, 'rb') as f:
        data = f.read()

    try:
        riff_size = struct.unpack('<I', data[4:8])[0]
        slack_start = 8 + riff_size
    except Exception as e:
        logger.error(f"{filename} RIFF 파싱 실패 → 건너뜀: {e}")
        return {
            "front": {"recovered": False, "frame_count": 0, "output_path": None},
            "rear": {"recovered": False, "frame_count": 0, "output_path": None}
        }
    
    result = {}

    for label, sig in [('front', FRONT_SIGNATURE), ('rear', REAR_SIGNATURE)]:
        chunks, count, sps, pps = extract_channel_from_slack(data, slack_start, sig)
        h264_path = os.path.join(output_h264_dir, f"{filename}_slack_{label}.h264")
        mp4_path = os.path.join(output_video_dir, f"{filename}_slack_{label}.{target_format}")

        write_chunks(h264_path, chunks, sps, pps)
        logger.info(f"{filename} → {label.upper()} 채널: {count}개 프레임 추출됨")

        if count > 0:
            success = convert_video(h264_path, mp4_path, target_format)
            result[label] = {
                "recovered": success,
                "frame_count": count,
                "output_path": mp4_path if success else None
            }
            if success:
                logger.info(f"{filename} → {label.upper()} 채널 복원 성공 → {mp4_path}")
            else:
                logger.warning(f"{filename} → {label.upper()} 채널 FFmpeg 변환 실패")
        else:
            if os.path.exists(h264_path):
                os.remove(h264_path)
            logger.info(f"{filename} → {label.upper()} 채널: 유효한 프레임 없음 (삭제됨)")

            result[label] = {
                "recovered": False,
                "frame_count": 0,
                "output_path": None
            }
    
    return result