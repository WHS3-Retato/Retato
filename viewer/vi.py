from flask import Flask, send_from_directory, jsonify, request
import os

app = Flask(__name__)

VIDEO_DIR = os.path.join(os.getcwd(), "extracted_media")

@app.route("/videos", methods=["GET"])
def list_videos():
    try:
        files = [f for f in os.listdir(VIDEO_DIR) if f.lower().endswith(('.mp4', '.avi'))]
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/stream/<path:filename>", methods=["GET"])
def stream_video(filename):
    # 프론트에서 특정 파일 클릭 시 영상 스트리밍
    return send_from_directory(VIDEO_DIR, filename)

if __name__ == "__main__":
    app.run(debug=True)