# Model Test Flask API

This project hosts a Flask API that exposes OCR and TTS endpoints.

## Contents

- `app.py` - Flask application
- `ocr_rapid_utils.py` - RapidOCR utilities
- `tts_utils.py` - Pocket‑TTS utilities

## Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### CPU-only install (avoid CUDA wheels)

Pocket‑TTS depends on PyTorch, and pip may default to CUDA-enabled wheels on Linux.
To force CPU-only wheels, install torch first from the CPU index, then install the rest:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

## Running the Server

```bash
source .venv/bin/activate
python app.py
```

The server listens on `http://localhost:5000`.

## Endpoints

### OCR (RapidOCR)

`POST /ocr-rapid`  
Multipart form with `file`.

```bash
curl -F "file=@/path/to/image.png" http://localhost:5000/ocr-rapid
```

### TTS (Pocket‑TTS)

`POST /tts`  
JSON body: `{ "text": "...", "voice": "alba" }`

```bash
curl -H "Content-Type: application/json" \
  -d '{"text":"Hello world","voice":"alba"}' \
  http://localhost:5000/tts --output tts.wav
```


## Notes

- Pocket‑TTS downloads the model on first use; the first request can take time.
- RapidOCR is usually the fastest OCR path on CPU.
- For Pocket‑TTS voices, use a built-in name like `alba` or a `hf://` URL.

### Pocket‑TTS performance

`torch.compile` is enabled by default when available (PyTorch 2.x). If it
causes issues on your machine, you can opt out:

```bash
export POCKET_TTS_TORCH_NOCOMPILE=1
```
