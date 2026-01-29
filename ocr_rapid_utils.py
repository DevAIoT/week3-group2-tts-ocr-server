from functools import lru_cache


@lru_cache(maxsize=1)
def _load_rapid_ocr():
    from rapidocr import RapidOCR

    return RapidOCR()


def run_rapid_ocr(image_path: str) -> str:
    engine = _load_rapid_ocr()
    result = engine(image_path)
    if result is None:
        return ""

    output = result[0] if isinstance(result, tuple) else result
    if hasattr(output, "txts"):
        txts = output.txts or ()
        return "\n".join(txts)

    lines = []
    for entry in output:
        if len(entry) >= 2:
            lines.append(entry[1])
    return "\n".join(lines)
