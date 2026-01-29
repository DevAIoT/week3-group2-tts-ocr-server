import os
from functools import lru_cache
from typing import Tuple

import torch

from pocket_tts import TTSModel


@lru_cache(maxsize=1)
def _load_model() -> TTSModel:
    model = TTSModel.load_model()
    if not os.getenv("POCKET_TTS_TORCH_NOCOMPILE", "").strip():
        compile_fn = getattr(torch, "compile", None)
        if compile_fn is not None:
            try:
                model = compile_fn(model)
            except Exception:
                # torch.compile is optional and may fail on some setups
                pass
    return model


@lru_cache(maxsize=16)
def _load_voice_state(voice: str):
    model = _load_model()
    return model.get_state_for_audio_prompt(voice)


def run_pocket_tts(text: str, voice: str = "alba") -> Tuple[torch.Tensor, int]:
    model = _load_model()
    voice_state = _load_voice_state(voice)
    audio = model.generate_audio(voice_state, text)
    return audio, model.sample_rate
