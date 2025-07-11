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

def extract_channel_by_signature(data, signature, valid_end):
    offset = 0
    count = 0
    extracted_chunks = []
    sps = pps = None # SPS, PPS 저장용

    while offset < valid_end:
        index = data.find(signature, offset, valid_end)
        if index == -1 or index + 8 > valid_end:
            break

        try:
            size = struct.unpack('<I', data[index + 4:index + 8])[0]
        except struct.error:
            logger.debug(f"프레임 size 언팩 실패 @ offset=0x{index:X}")
            offset = index + 1
            continue

        chunk_start = index + 8
        chunk_end = chunk_start + size

        # 사이즈 검사
        if size > MAX_REASONABLE_CHUNK_SIZE:
            logger.debug(f"비정상적으로 큰 프레임 (size={size}, offset=0x{index:X}) → skip")
            offset = index + 4
            continue

        if chunk_end - chunk_start < 5:
            logger.debug(f"너무 작은 프레임 (size={size}, offset=0x{index:X}) → skip")
            offset = index + 4
            continue

        if chunk_end > valid_end:
            logger.debug(f"프레임이 파일 끝을 넘어감 (size={size}, offset=0x{index:X}) → skip")
            offset = index + 4
            continue

        # NAL 헤더 검사
        nal_prefix = data[chunk_start:chunk_start + 4]
        if nal_prefix != b'\x00\x00\x00\x01':
            logger.debug(f"잘못된 NAL prefix (offset=0x{index:X}) → skip")
            offset = index + 4
            continue
        
        # SPS / PPS 저장
        nal_type = data[chunk_start + 4] & 0x1F
        if nal_type == 7:
            sps = data[chunk_start:chunk_end]
        elif nal_type == 8:
            pps = data[chunk_start:chunk_end]

        if nal_type in (1, 5, 7, 8):
            extracted_chunks.append(data[chunk_start:chunk_end])
            count += 1

        # 정렬 처리 (짝수 맞추기)
        aligned_size = size + (size % 2)
        offset = index + 8 + aligned_size

    return extracted_chunks, count, sps, pps

def write_chunks(filepath, chunks, sps=None, pps=None):
    with open(filepath, 'wb') as f:
        if sps and pps:
            f.write(sps)
            f.write(pps)
        for chunk in chunks:
            f.write(chunk)

def split_avi_channels(filepath, output_h264_dir, output_video_dir, target_format="mp4"):
    os.makedirs(output_h264_dir, exist_ok=True)
    os.makedirs(output_video_dir, exist_ok=True)

    filename = os.path.splitext(os.path.basename(filepath))[0]
    
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        real_file_size = struct.unpack('<I', data[4:8])[0]
        valid_end = 8 + real_file_size
    except struct.error:
        logger.error(f"{filename} → RIFF size 파싱 실패: {e}")
        return {
            "front": {"success": False, "frame_count": 0, "output_path": None},
            "rear": {"success": False, "frame_count": 0, "output_path": None}
        }
    
    result = {}

    for label, sig in [('front', FRONT_SIGNATURE), ('rear', REAR_SIGNATURE)]:
        chunks, count, sps, pps = extract_channel_by_signature(data, sig, valid_end)
        h264_path = os.path.join(output_h264_dir, f"{filename}_{label}.h264")
        mp4_path = os.path.join(output_video_dir, f"{filename}_{label}.{target_format}")

        write_chunks(h264_path, chunks, sps, pps)
        logger.info(f"{filename} → {label.upper()} 채널: {count}개 프레임 추출")

        if count > 0:
            success = convert_video(h264_path, mp4_path, target_format)
            result[label] = {
                "success": success,
                "frame_count": count,
                "output_path": mp4_path if success else None
            }
            if success:
                logger.info(f"{filename} → {label.upper()} 채널 복원 성공 → {mp4_path}")
            else:
                logger.warning(f"{filename} → {label.upper()} 채널 FFmpeg 변환 실패")
        else:
            logger.info(f"{filename} → {label.upper()} 채널: 유효한 프레임 없음 (변환 생략)")
            result[label] = {
                "success": False,
                "frame_count": 0,
                "output_path": None
            }

    return result