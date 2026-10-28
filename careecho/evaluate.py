"""Evaluate frozen synthetic cases. This is a diagnostic set, not clinical validation."""

import hashlib
import json
from pathlib import Path

from .metrics import classification_metrics
from .nlp import review
from .schema import Plan


def evaluate(dataset: str | Path) -> dict:
    root = Path(dataset)
    raw = (root / "cases.json").read_bytes()
    cases = json.loads(raw)
    plans = {
        p.stem: Plan.model_validate_json(p.read_text(encoding="utf-8"))
        for p in (root / "plans").glob("*.json")
    }
    pairs, failures = [], []
    barrier_tp = barrier_fp = barrier_fn = 0
    for case in cases:
        result = review(plans[case["plan"]], case["transcript"])
        expected = case["expected"]
        if set(expected) != {t.id for t in plans[case["plan"]].targets}:
            raise ValueError(f"Incomplete labels in {case['id']}")
        for finding in result.findings:
            truth = expected[finding.target_id]
            pairs.append((truth, finding.status))
            if truth != finding.status:
                failures.append(
                    dict(
                        case=case["id"],
                        target=finding.target_id,
                        expected=truth,
                        predicted=finding.status,
                    )
                )
        gold = set(case["barriers"])
        pred = {b.category for b in result.barriers}
        barrier_tp += len(gold & pred)
        barrier_fp += len(pred - gold)
        barrier_fn += len(gold - pred)
    plan_bytes = b"".join(p.read_bytes() for p in sorted((root / "plans").glob("*.json")))
    return dict(
        engine="rules-v1",
        dataset_sha256=hashlib.sha256(raw + plan_bytes).hexdigest(),
        cases=len(cases),
        scope="Hand-authored synthetic diagnostic cases; not held-out clinical data",
        classification=classification_metrics(pairs),
        barriers=dict(
            true_positive=barrier_tp, false_positive=barrier_fp, false_negative=barrier_fn
        ),
        failures=failures,
    )
