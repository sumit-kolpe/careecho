# Demo and study guide

## A three-minute walkthrough

1. Launch the app. Explain the distinction between a reference care plan and a
   patient's teach-back. Emphasize the synthetic-data scope.
2. Select `wound-cost-and-ride` and review. Show the medication conflict, exact quote,
   and cost/transportation concerns. Explain why a person can recall a visit yet lack a ride.
3. Change “once a day” to “twice daily” and review again. Show that evidence matching
   changes but practical barriers remain.
4. Upload `data/audio/teachback.wav`, run local Whisper, inspect the text, then review.
   Explain that ASR errors propagate into downstream classifications.
5. Show `reports/baseline.json` and `docs/RESULTS.md`, including errors. Explain why
   one synthetic voice is a smoke test rather than a medical ASR benchmark.

## Be ready to explain

- Why reference-document agreement is different from word error rate.
- Why a quote check establishes provenance but not semantic correctness.
- How negation, numerical details, and self-corrections affect safety.
- Why glossary prompting needs an ablation rather than an assumed benefit.
- How you would prevent template and speaker leakage in evaluation.
- What runs locally and what the optional API transmits.
- Which parts are rules, pretrained inference, and untested extensions.

## Make the project your own

Read the code, reproduce the commands, and add an independently designed experiment
before claiming expertise. Good contributions include a new plan with 10 independently
labeled paraphrases, a subject-attribution failure analysis, or a richer frequency
normalizer with documented precision/recall tradeoffs. Record your experiment and
what failed. Keep AI assistance transparent.

Possible application description, after you have run and understood the project:

> I developed and evaluated CareEcho, an AI-assisted research prototype for reviewing
> synthetic discharge teach-back. It combines local Whisper inference, an evidence-linked
> NLP baseline, an optional structured LLM API adapter, and an evaluation harness.
> I explored how speech errors and phrasing affect review results and surfaced
> practical care barriers such as cost and transportation. The work uses synthetic
> data and has not been clinically validated.

Adjust “developed and evaluated” to accurately describe your own contribution.
Do not describe it as deployed at a hospital, Penn-affiliated, HIPAA-compliant,
fine-tuned, or clinically validated.
