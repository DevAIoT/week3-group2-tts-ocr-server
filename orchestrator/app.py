import logging
import os
import time
import uuid
from threading import Lock
from typing import Iterable, List

import requests
from flask import Flask, Response, jsonify, request


def _load_targets() -> List[str]:
    targets_file = os.getenv("ORCH_TARGETS_FILE", "targets.txt")
    if not os.path.isabs(targets_file):
        targets_file = os.path.join(os.path.dirname(__file__), targets_file)

    targets = []
    try:
        with open(targets_file, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                targets.append(line.rstrip("/"))
    except FileNotFoundError:
        pass
    return targets


TARGETS = _load_targets()
_rr_lock = Lock()
_rr_index = 0

CONNECT_TIMEOUT = float(os.getenv("ORCH_CONNECT_TIMEOUT", "5"))
READ_TIMEOUT = float(os.getenv("ORCH_READ_TIMEOUT", "120"))

app = Flask(__name__)
LOG_LEVEL = os.getenv("ORCH_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("orchestrator")


def _rotated_targets() -> Iterable[str]:
    global _rr_index
    if not TARGETS:
        return []
    with _rr_lock:
        start = _rr_index
        _rr_index = (_rr_index + 1) % len(TARGETS)
    return [TARGETS[(start + i) % len(TARGETS)] for i in range(len(TARGETS))]


def _forward_request(
    method: str,
    path: str,
    *,
    json_body=None,
    files=None,
):
    last_error = None
    request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex
    for base_url in _rotated_targets():
        url = f"{base_url}{path}"
        try:
            logger.info("forward_start id=%s url=%s", request_id, url)
            resp = requests.request(
                method=method,
                url=url,
                json=json_body,
                files=files,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            logger.info(
                "forward_done id=%s url=%s status=%s",
                request_id,
                url,
                resp.status_code,
            )
            if resp.status_code < 500:
                return resp
            logger.warning(
                "forward_retry id=%s url=%s status=%s",
                request_id,
                url,
                resp.status_code,
            )
        except requests.RequestException as exc:
            last_error = exc
            logger.warning("forward_error id=%s url=%s err=%s", request_id, url, exc)
            continue
    if last_error:
        raise last_error
    raise RuntimeError("No targets configured for orchestrator")


def _proxy_response(resp: requests.Response) -> Response:
    content_type = resp.headers.get("Content-Type", "application/octet-stream")
    return Response(resp.content, status=resp.status_code, content_type=content_type)


@app.get("/health")
def health():
    return jsonify({"targets": TARGETS, "count": len(TARGETS)})


@app.before_request
def _log_request_start():
    request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex
    request.environ["request_id"] = request_id
    request.environ["start_time"] = time.monotonic()
    logger.info("request_start id=%s method=%s path=%s", request_id, request.method, request.path)


@app.after_request
def _log_request_end(response):
    request_id = request.environ.get("request_id", "-")
    start_time = request.environ.get("start_time")
    elapsed_ms = None
    if start_time is not None:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
    logger.info(
        "request_done id=%s method=%s path=%s status=%s elapsed_ms=%s",
        request_id,
        request.method,
        request.path,
        response.status_code,
        elapsed_ms,
    )
    return response


@app.post("/tts")
def tts_proxy():
    payload = request.get_json(silent=True) or {}
    resp = _forward_request("POST", "/tts", json_body=payload)
    return _proxy_response(resp)


@app.post("/tts-kokoro")
def tts_kokoro_proxy():
    payload = request.get_json(silent=True) or {}
    resp = _forward_request("POST", "/tts-kokoro", json_body=payload)
    return _proxy_response(resp)


@app.post("/ocr-rapid")
def ocr_rapid_proxy():
    if "file" not in request.files:
        return jsonify({"error": "Missing file field"}), 400

    file_storage = request.files["file"]
    if not file_storage or file_storage.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    files = {
        "file": (file_storage.filename, file_storage.read(), file_storage.mimetype),
    }
    resp = _forward_request("POST", "/ocr-rapid", files=files)
    return _proxy_response(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6001, debug=True, threaded=True)
