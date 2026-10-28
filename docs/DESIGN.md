# Design and limitations

## Why this workflow

Scribing asks “what was said?” Teach-back review additionally asks “which reference
details were restated, which need clarification, and what makes follow-through hard?”
This creates a focused speech/NLP problem without asking a model to invent care.

Reference targets are manually structured because parsing arbitrary discharge
documents introduces another extraction error source. Each has an instruction,
topic anchors, required groups of alternative phrases, known conflicting phrases,
and a human-authored follow-up question.

## Baseline decisions

Unicode and punctuation normalization supports exact phrase matching with token
boundaries. Original text is retained for evidence offsets. Relevant sentences must
contain a topic anchor. A known conflict takes priority, then uncertainty/negation,
then complete same-sentence concept coverage, then partial coverage. Absent anchors
are marked missing. Same-sentence matching limits accidental joining across topics,
but it misses valid explanations spread across sentences.

This baseline cannot robustly resolve subject attribution, temporal scope, nested
negation, corrections, arbitrary doses, or medical synonyms. For example, “My sister
takes cephalexin twice daily for five days” can be marked covered even though it says
nothing about the speaker's plan. A word outside the configured conflict lexicon can
also evade detection. These are reasons for mandatory review, not a reliable safety
filter. The small diagnostic set does not exhaust these failure modes.

## LLM contract

The API receives plan and transcript as data, with explicit instructions not to follow
embedded commands. Pydantic structured output constrains syntax. Post-validation
requires every known target exactly once, evidence for non-missing findings, no
evidence for missing findings, and exact transcript substrings. Duplicate quotes
map to the first matching occurrence. Questions come from the plan, not generation.

This prevents some fabricated evidence and structural errors. It does not prevent a
model from citing irrelevant real text or generating an incorrect explanation.
Prompt injection resistance and semantic correctness are not guaranteed. The API
adapter is optional and never invoked by the default reviewer or evaluation command.

## Audio and evaluation

Whisper weights run locally through CTranslate2. English and CPU INT8 are explicit
prototype choices. VAD removes candidate non-speech, but neither VAD nor average
log probability proves correctness. Silence may still yield hallucinated words.
Vocabulary hints can improve spelling or bias output; the experiment measures both
with and without hints. No automatic medical spelling correction is applied.

WER uses normalized word-level Levenshtein distance (substitutions + deletions +
insertions divided by reference word count). Numbers are not mapped from words to
digits. Vocabulary recall is exact normalized presence of four selected terms; it
does not measure correctness of surrounding doses. Downstream agreement compares
ASR-derived rule statuses with reference-text rule statuses, not clinical ground truth.

Classification macro F1 averages only classes represented in ground truth. The
unsafe-coverage count is a diagnostic count of non-covered labels predicted covered;
zero on a tiny fixture is not a safety claim. Reports retain each mismatch and the
confusion matrix. No train/test generalization claim is made.

## Extension plan

1. Obtain independent labels for a larger synthetic set before tuning the baseline.
2. Split by scenario/template and speaker, not random paraphrases of identical text.
3. Add slot-level extraction for dose, frequency, duration, and timing with abstention.
4. Benchmark paired baseline and LLM results, including refusals, latency, and cost.
5. Evaluate real consenting speakers only under appropriate research approval.
6. Assess reviewer usability and subgroup error rates before considering clinical deployment.
