import tempfile

from flask import Flask, jsonify, request, send_file

from ocr_rapid_utils import run_rapid_ocr
from tts_utils import run_pocket_tts


app = Flask(__name__)


@app.post("/ocr-rapid")
def ocr_rapid_endpoint():
    if "file" not in request.files:
        return jsonify({"error": "Missing file field"}), 400

    file_storage = request.files["file"]
    if not file_storage or file_storage.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        file_storage.save(tmp.name)
        image_path = tmp.name

    text = run_rapid_ocr(image_path)
    return jsonify({"text": text})


@app.post("/tts")
def tts_endpoint():
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "").strip()
    if not text:
        return jsonify({"error": "Missing text"}), 400

    voice = payload.get("voice", "alba")
    audio, sample_rate = run_pocket_tts(text, voice=voice)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        output_path = tmp.name

    import soundfile as sf

    sf.write(output_path, audio.numpy(), sample_rate)
    return send_file(
        output_path,
        mimetype="audio/wav",
        as_attachment=True,
        download_name="tts.wav",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
