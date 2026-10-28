"""Reproducible clean/noise x glossary ablation on one synthetic recording."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import random
import struct
import wave
from pathlib import Path

from careecho.audio import transcribe
from careecho.metrics import word_errors
from careecho.nlp import contains, review
from careecho.schema import Plan


def noisy_copy(source: Path, destination: Path, snr_db: float = 10.0):
    with wave.open(str(source), "rb") as wav:
        params = wav.getparams()
        if params.sampwidth != 2:
            raise ValueError("Noise experiment requires 16-bit PCM")
        raw = wav.readframes(params.nframes)
    samples = struct.unpack(f"<{len(raw) // 2}h", raw)
    rms = (sum(v * v for v in samples) / len(samples)) ** 0.5
    noise_rms = rms / (10 ** (snr_db / 20))
    rng = random.Random(42)
    noisy = [max(-32768, min(32767, round(v + rng.gauss(0, noise_rms)))) for v in samples]
    with wave.open(str(destination), "wb") as wav:
        wav.setparams(params)
        wav.writeframes(struct.pack(f"<{len(noisy)}h", *noisy))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="tiny.en")
    parser.add_argument("--output", default="reports/asr_experiment.json")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / "data/audio/teachback.wav"
    noisy = root / "outputs/teachback-noisy.wav"
    noisy.parent.mkdir(exist_ok=True)
    noisy_copy(source, noisy)
    reference = (root / "data/sample_transcript.txt").read_text(encoding="utf-8").strip()
    plan = Plan.model_validate_json((root / "data/plans/wound.json").read_text())
    baseline = {f.target_id: f.status for f in review(plan, reference).findings}
    terms = ["cephalexin", "dressing", "clinic", "prescription"]
    rows = []
    for condition, audio in [("clean", source), ("noise_10db_seed42", noisy)]:
        for glossary in ["", "cephalexin, dressing, clinic, prescription"]:
            transcript = transcribe(audio, args.model, glossary)
            errors, words = word_errors(reference, transcript.text)
            findings = review(plan, transcript.text).findings
            rows.append(
                dict(
                    condition=condition,
                    glossary=bool(glossary),
                    errors=errors,
                    reference_words=words,
                    wer=errors / words,
                    term_recall=sum(contains(transcript.text, t) for t in terms) / len(terms),
                    downstream_status_agreement=sum(
                        f.status == baseline[f.target_id] for f in findings
                    )
                    / len(findings),
                    transcription=transcript.model_dump(),
                )
            )
            print(f"{condition} glossary={bool(glossary)} WER={errors / words:.3f}", flush=True)
    result = dict(
        scope="One synthetic TTS voice and one script, not a clinical ASR benchmark",
        python=platform.python_version(),
        platform=platform.platform(),
        versions={
            p: importlib.metadata.version(p)
            for p in ["faster-whisper", "ctranslate2", "huggingface-hub"]
        },
        audio_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        reference=reference,
        terms=terms,
        model=args.model,
        rows=rows,
    )
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
