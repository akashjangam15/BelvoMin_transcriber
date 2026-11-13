"""
Speech-to-text module for the meeting intelligence platform.

Input : path to an audio file (mp3, wav, m4a, ...)
Output: a dict (also saved as JSON) with the full transcript and timestamped
        segments, which downstream modules (summary, speaker identification,
        decisions, action items, PDF report) can consume.

Install:  pip install faster-whisper
Use as a library:
    from transcriber import transcribe_audio
    result = transcribe_audio("meeting.mp3")
Use from the command line:
    python transcriber.py meeting.mp3 --model small --out transcript.json
"""

import argparse
import json
import logging
import os
import time
from functools import lru_cache
from pathlib import Path

from faster_whisper import WhisperModel

log = logging.getLogger("transcriber")

SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".mp4", ".webm"}


def _pick_device():
    """Use the GPU if one is available, otherwise the CPU.

    Set the environment variable TRANSCRIBER_DEVICE=cpu to force the CPU
    (useful when a GPU is present but its CUDA libraries are not set up).
    """
    if os.environ.get("TRANSCRIBER_DEVICE", "").lower() == "cpu":
        return "cpu", "int8"
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"  # int8 keeps CPU inference fast and memory-light


@lru_cache(maxsize=2)
def _load_model(model_size):
    """Load the model once and reuse it (loading is slow, so never do it per request)."""
    device, compute_type = _pick_device()
    log.info("Loading model '%s' on %s (%s)", model_size, device, compute_type)
    return WhisperModel(model_size, device=device, compute_type=compute_type)


def _format_ts(seconds):
    s = int(seconds)
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def transcribe_audio(audio_path, model_size="small", language=None):
    """
    Transcribe one audio file.

    model_size: tiny | base | small | medium | large-v3
                (small is a good accuracy/speed balance on a laptop CPU)
    language:   e.g. "en", "hi". None means auto-detect.
    """
    path = Path(audio_path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported audio format: {path.suffix}")
    if path.stat().st_size == 0:
        raise ValueError(f"Audio file is empty: {path}")

    model = _load_model(model_size)
    started = time.time()

    segments_iter, info = model.transcribe(
        str(path),
        language=language,
        beam_size=5,
        vad_filter=True,  # skips silence, which also reduces hallucinated text
        vad_parameters={"min_silence_duration_ms": 500},
    )

    # segments_iter is lazy: the real work happens while we loop over it
    segments = []
    for i, seg in enumerate(segments_iter):
        text = seg.text.strip()
        if not text:
            continue
        segments.append(
            {
                "id": i,
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": text,
            }
        )

    elapsed = time.time() - started
    result = {
        "audio_file": path.name,
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "duration_seconds": round(info.duration, 2),
        "model": model_size,
        "processing_seconds": round(elapsed, 2),
        "full_text": " ".join(s["text"] for s in segments),
        "segments": segments,
    }
    log.info(
        "Done: %.0fs of audio in %.0fs, %d segments",
        info.duration,
        elapsed,
        len(segments),
    )
    return result


def save_outputs(result, out_json):
    """Write the JSON result plus a human-readable .txt with timestamps."""
    out_json = Path(out_json)
    out_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [f"[{_format_ts(s['start'])}] {s['text']}" for s in result["segments"]]
    out_json.with_suffix(".txt").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Transcribe a meeting recording.")
    parser.add_argument("audio", help="Path to the audio file")
    parser.add_argument("--model", default="small", help="tiny, base, small, medium, large-v3")
    parser.add_argument("--language", default=None, help="Language code, e.g. en. Default: auto-detect")
    parser.add_argument("--out", default=None, help="Output JSON path (default: <audio name>.json)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    result = transcribe_audio(args.audio, model_size=args.model, language=args.language)
    out = args.out or str(Path(args.audio).with_suffix(".json"))
    save_outputs(result, out)
    print(f"Saved {out} and {Path(out).with_suffix('.txt')}")


if __name__ == "__main__":
    main()