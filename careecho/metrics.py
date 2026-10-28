"""Dependency-free error metrics; aggregate counts before computing corpus WER."""

from .nlp import normalize


def word_errors(reference: str, hypothesis: str) -> tuple[int, int]:
    ref, hyp = normalize(reference).split(), normalize(hypothesis).split()
    row = list(range(len(hyp) + 1))
    for i, a in enumerate(ref, 1):
        new = [i]
        for j, b in enumerate(hyp, 1):
            new.append(min(new[-1] + 1, row[j] + 1, row[j - 1] + (a != b)))
        row = new
    return row[-1], len(ref)


def classification_metrics(pairs: list[tuple[str, str]]) -> dict:
    labels = ["covered", "missing", "needs_review", "possible_conflict"]
    confusion = {truth: {pred: 0 for pred in labels} for truth in labels}
    for truth, pred in pairs:
        confusion[truth][pred] += 1
    per_class = {}
    for label in labels:
        tp = confusion[label][label]
        support = sum(confusion[label].values())
        predicted = sum(confusion[t][label] for t in labels)
        precision = tp / predicted if predicted else 0
        recall = tp / support if support else 0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
        per_class[label] = dict(precision=precision, recall=recall, f1=f1, support=support)
    supported = [v["f1"] for v in per_class.values() if v["support"]]
    return dict(
        n=len(pairs),
        accuracy=sum(t == p for t, p in pairs) / len(pairs) if pairs else 0,
        macro_f1=sum(supported) / len(supported) if supported else 0,
        unsafe_coverage_count=sum(t != "covered" and p == "covered" for t, p in pairs),
        per_class=per_class,
        confusion=confusion,
    )
