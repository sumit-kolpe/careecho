"""Local WAV quality inspection and Hugging Face-hosted Whisper inference."""

import math
import struct
import time
import wave
from pathlib import Path

from .schema import Segment, Transcription


def inspect_wav(path: str | Path) -> dict:
    path = Path(path)
    if path.stat().st_size > 25 * 1024 * 1024:
        raise ValueError("WAV exceeds 25 MB")
    try:
        with wave.open(str(path), "rb") as wav:
            channels, width, rate, frames = (
                wav.getnchannels(),
                wav.getsampwidth(),
                wav.getframerate(),
                wav.getnframes(),
            )
            if width != 2 or channels not in (1, 2):
                raise ValueError("Use mono or stereo 16-bit PCM WAV")
            duration = frames / rate
            if not 0.25 <= duration <= 180:
                raise ValueError("Audio must be between 0.25 and 180 seconds")
            raw = wav.readframes(frames)
    except (wave.Error, EOFError) as exc:
        raise ValueError("Invalid PCM WAV") from exc
    if len(raw) != frames * channels * width:
        raise ValueError("Truncated WAV payload")
    samples = struct.unpack(f"<{len(raw) // 2}h", raw)
    rms = math.sqrt(sum((v / 32768) ** 2 for v in samples) / len(samples))
    clipping = sum(abs(v) >= 32760 for v in samples) / len(samples)
    warnings = []
    if rms < 0.008:
        warnings.append("Low audio level: inspect transcription carefully.")
    if clipping > 0.01:
        warnings.append("Clipping detected: speech detail may be lost.")
    return dict(
        sample_rate=rate,
        channels=channels,
        duration_seconds=round(duration, 3),
        rms=round(rms, 5),
        clipped_fraction=round(clipping, 5),
        warnings=warnings,
    )


def transcribe(path: str | Path, model: str = "tiny.en", glossary: str = "") -> Transcription:
    quality = inspect_wav(path)
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError('Install ASR support: pip install -e ".[asr]"') from exc
    started = time.perf_counter()
    engine = WhisperModel(model, device="cpu", compute_type="int8")
    # Glossary is optional: it can help recognition but can also bias/hallucinate terms.
    segments, info = engine.transcribe(
        str(path),
        language="en",
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False,
        initial_prompt=glossary or None,
    )
    output = [
        Segment(
            start=s.start,
            end=s.end,
            text=s.text.strip(),
            avg_logprob=s.avg_logprob,
            no_speech_prob=s.no_speech_prob,
        )
        for s in segments
    ]
    warnings = list(quality["warnings"])
    if any(s.avg_logprob < -1 or s.no_speech_prob > 0.6 for s in output):
        warnings.append(
            "Some ASR segments have weak scores; these are not calibrated confidence values."
        )
    if not output:
        warnings.append("No speech segments detected.")
    return Transcription(
        text=" ".join(s.text for s in output),
        model=model,
        language=info.language,
        duration_seconds=quality["duration_seconds"],
        elapsed_seconds=round(time.perf_counter() - started, 3),
        segments=output,
        warnings=warnings,
    )
