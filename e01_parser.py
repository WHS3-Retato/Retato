import pyewf
import pytsk3
import os

class EWFImgInfo(pytsk3.Img_Info):
    def __init__(self, ewf_handle):
        self._ewf_handle = ewf_handle
        super(EWFImgInfo, self).__init__("", pytsk3.TSK_IMG_TYPE_EXTERNAL)

    def read(self, offset, size):
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        return self._ewf_handle.get_media_size()

def open_e01_image(e01_path):
    filenames = pyewf.glob(e01_path)
    ewf_handle = pyewf.handle()
    ewf_handle.open(filenames)
    return EWFImgInfo(ewf_handle)

def extract_mp4_files(fs_info, output_dir, path="/"):
    directory = fs_info.open_dir(path=path)
    for entry in directory:
        if entry.info.name.name in [b'.', b'..'] or entry.info.meta is None:
            continue

        name = entry.info.name.name.decode('utf-8', 'ignore')
        filepath = os.path.join(path, name)

        if entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
            try:
                sub_directory = entry.as_directory()
                extract_mp4_files(fs_info, output_dir, filepath)
            except Exception as e:
                print(f"[Skip] Cannot access directory: {filepath} - {e}")
        elif name.lower().endswith('.mp4'):
            print(f"\n[Found] MP4 file detected: {filepath}")
            try:
                f = fs_info.open(filepath)
                out_path = os.path.join(output_dir, name)
                with open(out_path, 'wb') as out_file:
                    offset = 0
                    size = f.info.meta.size
                    while offset < size:
                        chunk = f.read_random(offset, min(1024 * 1024, size - offset))
                        out_file.write(chunk)
                        offset += len(chunk)
                print(f"[Extracted] Saved to: {out_path}")
                print("-" * 60)
            except Exception as e:
                print(f"[Error] Failed to extract {filepath}: {e}")
                print("-" * 60)


def main():
    e01_path = r"D:\test.E01" # E01 경로
    output_dir = r".\extracted_mp4" # 추출 영상 저장 경로
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n[Info] Opening E01 image: {e01_path}")
    img_info = open_e01_image(e01_path)

    print("\n[Info] Scanning partitions...")
    volume = pytsk3.Volume_Info(img_info)
    found = False

    for part in volume:
        print(f"\n[Try] Partition: desc={part.desc}, start={part.start}, length={part.len}")
        try:
            fs_offset = part.start * 512
            fs_info = pytsk3.FS_Info(img_info, offset=fs_offset)
            extract_mp4_files(fs_info, output_dir)
            print("\n 🥔 [Success] Partition opened and processed. 🥔")
            found = True
            break
        except Exception as e:
            print(f"[Fail] Could not open partition: {e}")

    if not found:
        print("\n[Result] No supported partition was found.")


if __name__ == "__main__":
    main()
