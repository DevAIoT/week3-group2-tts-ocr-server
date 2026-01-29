import subprocess
from typing import Optional


def run_kokoro_tts(
    text: str,
    output_path: str,
    voice: Optional[str] = None,
    lang: Optional[str] = None,
    speed: Optional[float] = None,
) -> None:
    cmd = ["kokoro-tts", "-", output_path]
    if voice:
        cmd.extend(["--voice", voice])
    if lang:
        cmd.extend(["--lang", lang])
    if speed is not None:
        cmd.extend(["--speed", str(speed)])

    try:
        subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "kokoro-tts CLI not found. Install it and ensure it's on PATH."
        ) from exc
