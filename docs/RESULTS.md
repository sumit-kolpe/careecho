# Measured results

Run on 2026-10-27 using Python 3.12.6 on Windows. See `requirements-tested.txt`
for the tested dependency snapshot. The repository was published on October 28, 2026;
current GitHub Actions results are available on the
[Actions page](https://github.com/sumit-kolpe/careecho/actions).

## Text diagnostic set

16 hand-authored synthetic cases, 2 plans, 42 target labels. Rules and cases were
developed together; this is not a held-out evaluation or evidence of clinical quality.

| Metric | Observed |
|---|---:|
| Target status accuracy | 40 / 42 (95.24%) |
| Macro F1 | 0.9482 |
| Non-covered labels incorrectly predicted covered | 0 / 25 |
| Barrier true positives | 6 |
| Barrier false positives | 1 |
| Barrier false negatives | 0 |

The two target mismatches are a paraphrase (“morning and evening”) and a self-correction
(“once a day, sorry, twice daily”). The barrier false positive is “It is not true that
I have no ride.” These failures are preserved rather than removed to improve scores.
Zero false coverage on this tiny fixture does not establish safety: subject attribution
and unlisted conflicts are known unmeasured weaknesses. Raw results and confusion
matrix: [baseline.json](../reports/baseline.json).

## Actual local Whisper experiment

`tiny.en`, CPU INT8, English, beam size 5, VAD. One 13.62-second synthetic voice recording,
37 normalized reference words, four vocabulary terms. Noise uses seed 42 and nominal
10 dB whole-file SNR. Model loading is included in elapsed times in the raw report.

| Audio | Vocabulary hint | Word errors / 37 | WER | Term recall | Downstream agreement |
|---|---|---:|---:|---:|---:|
| Clean | No | 1 | 2.70% | 75% | 2 / 3 |
| Clean | Yes | 0 | 0.00% | 100% | 1 / 3 |
| Noisy | No | 2 | 5.41% | 75% | 2 / 3 |
| Noisy | Yes | 0 | 0.00% | 100% | 1 / 3 |

The hint was the vocabulary list “cephalexin, dressing, clinic, prescription”; it did
not contain the reference sentence. Without it, the clean audio transcribed the drug
as “Cephaluxen,” causing the rule engine to miss the medication topic.

**Why perfect WER did not mean a better downstream result:** the hinted transcript
joined several instructions with commas instead of periods. WER normalization removes
punctuation, so the words match perfectly. The sentence-based baseline then scopes a
conflict/negation too broadly across instructions. This experiment demonstrates the
need to measure downstream errors and clause/slot structure, not just WER.

The result does not establish that hints help in general or that Whisper is accurate
for medical conversations. There is no speaker diversity, real background noise,
overlap, independent audio corpus, or confidence interval. Raw transcripts, segment
timestamps, scores, package versions, and recording hash:
[asr_experiment.json](../reports/asr_experiment.json).

## Verification

- 27 automated tests passed: evidence offsets, conflicting/negated language, plan
  contracts, WER, audio checks, cloud opt-in, fabricated-quote rejection, API refusal,
  mocked structured API request, and app review/edit flow.
- Ruff checks passed.
- Editable package installation succeeded.
- Actual local model download and all four ASR inference conditions completed.
- Browser review verified the conflict, source quotes, and access-barrier output.
- The OpenAI adapter was tested with mocked responses; no live API call or LLM quality
  benchmark was performed because no user-provided API credentials were supplied.

The Windows sandbox blocked loopback sockets used by Streamlit. Full interface tests
and the local demo were run outside that sandbox; this required no application-code
workaround. PyAV 19 was incompatible with faster-whisper's decoding call; the ASR
extra now constrains PyAV below 17, and inference was verified with 16.1.0.

Reproduce text metrics with `python -m careecho.cli evaluate` and audio metrics with
`python -m scripts.asr_experiment`. Scores can change with model versions, dependencies,
or regenerated synthetic voices. Preserve the recording and compare its stored hash.
