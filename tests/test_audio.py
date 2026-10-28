import struct
import wave

import pytest

from careecho.audio import inspect_wav


def wav_file(path, samples, width=2):
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(width)
        wav.setframerate(16000)
        wav.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def test_silence_warning(tmp_path):
    path = tmp_path / "silence.wav"
    wav_file(path, [0] * 16000)
    result = inspect_wav(path)
    assert result["duration_seconds"] == 1
    assert "Low audio" in result["warnings"][0]


def test_clipping_warning(tmp_path):
    path = tmp_path / "clip.wav"
    wav_file(path, [32767] * 16000)
    assert inspect_wav(path)["clipped_fraction"] == 1


def test_short_audio_rejected(tmp_path):
    path = tmp_path / "short.wav"
    wav_file(path, [0] * 10)
    with pytest.raises(ValueError, match="180 seconds"):
        inspect_wav(path)


def test_invalid_audio(tmp_path):
    path = tmp_path / "invalid.wav"
    path.write_bytes(b"not a wav")
    with pytest.raises(ValueError, match="Invalid"):
        inspect_wav(path)
