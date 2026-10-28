"""Transparent, conservative phrase baseline; no learned clinical knowledge."""

import re
import unicodedata

from .schema import Barrier, Evidence, Finding, Plan, Report


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower().replace("’", "'")
    text = re.sub(r"\b(can't|cannot)\b", "can not", text)
    text = re.sub(r"\b(won't)\b", "will not", text)
    text = re.sub(r"n't\b", " not", text)
    return " ".join(re.findall(r"\w+(?:\.\d+)?", text))


def contains(text: str, phrase: str) -> bool:
    return f" {normalize(phrase)} " in f" {normalize(text)} "


def sentences(text: str) -> list[Evidence]:
    # Preserve exact offsets; do not split decimal doses such as 2.5.
    pattern = r"[^!?\n]+?(?:[!?]|(?<!\d)\.(?!\d)|\n|$)"
    spans = []
    for match in re.finditer(pattern, text):
        raw = match.group()
        quote = raw.strip()
        if quote:
            start = match.start() + len(raw) - len(raw.lstrip())
            spans.append(Evidence(quote=quote, start=start, end=start + len(quote)))
    return spans


BARRIER_RULES = {
    "transport": (
        ["no ride", "no car", "cannot get to", "can't get to", "bus does not"],
        "What transportation help would make the follow-up visit possible?",
    ),
    "cost": (
        ["cannot afford", "can't afford", "too expensive", "no insurance", "costs too much"],
        "Would you like the care team to discuss medication or visit costs?",
    ),
    "language": (
        ["cannot read", "can't read", "need an interpreter", "do not understand english"],
        "Which language or format would make these instructions easier to use?",
    ),
    "support": (
        ["live alone", "no one to help", "nobody to help"],
        "Who could help you carry out this plan at home?",
    ),
}


def barriers_in(text: str) -> list[Barrier]:
    result = []
    for category, (phrases, question) in BARRIER_RULES.items():
        for span in sentences(text):
            if any(contains(span.quote, phrase) for phrase in phrases):
                result.append(Barrier(category=category, evidence=span, question=question))
                break
    return result


def review(plan: Plan, transcript: str) -> Report:
    if len(transcript) > 30_000:
        raise ValueError("Transcript exceeds the 30,000-character prototype limit")
    spans = sentences(transcript)
    findings = []
    for target in plan.targets:
        relevant = [s for s in spans if any(contains(s.quote, a) for a in target.anchors)]
        conflicts = [s for s in relevant if any(contains(s.quote, c) for c in target.conflicts)]
        # Full coverage must occur in a single sentence to limit accidental cross-topic joins.
        complete = [
            s
            for s in relevant
            if all(any(contains(s.quote, phrase) for phrase in group) for group in target.concepts)
        ]
        uncertain = [
            s
            for s in relevant
            if any(
                contains(s.quote, p)
                for p in ["not", "never", "no", "maybe", "unsure", "i think", "or", "instead"]
            )
        ]
        if conflicts:
            status, evidence, reason = (
                "possible_conflict",
                conflicts,
                "Configured conflict phrase found.",
            )
        elif uncertain:
            status, evidence, reason = (
                "needs_review",
                relevant,
                "Negation or uncertainty needs review.",
            )
        elif complete:
            status, evidence, reason = (
                "covered",
                complete,
                "All configured concepts found together.",
            )
        elif relevant:
            status, evidence, reason = (
                "needs_review",
                relevant,
                "Topic mentioned; required details are incomplete.",
            )
        else:
            status, evidence, reason = "missing", [], "No configured topic anchor found."
        findings.append(
            Finding(
                target_id=target.id,
                status=status,
                evidence=evidence,
                reason=reason,
                question=target.question,
            )
        )
    warnings = [
        "Research prototype: every result needs human review; covered does not establish understanding."
    ]
    if not transcript.strip():
        warnings.append("Empty transcript: no evidence available.")
    return Report(
        plan_id=plan.id,
        engine="rules-v1",
        transcript=transcript,
        findings=findings,
        barriers=barriers_in(transcript),
        warnings=warnings,
    )
