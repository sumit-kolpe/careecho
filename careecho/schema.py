"""Explicit contracts for clinician-authored targets and evidence-linked review."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Target(StrictModel):
    id: str = Field(min_length=1)
    category: Literal["medication", "follow_up", "self_care", "warning_sign"]
    instruction: str = Field(min_length=1)
    # Every group must match; each group contains alternate surface forms.
    concepts: list[list[str]] = Field(min_length=1)
    anchors: list[str] = Field(min_length=1)
    conflicts: list[str] = Field(default_factory=list)
    question: str = Field(min_length=1)

    @model_validator(mode="after")
    def nonempty_terms(self):
        if any(not group or any(not s.strip() for s in group) for group in self.concepts):
            raise ValueError("Concept groups must contain nonempty phrases")
        if any(not s.strip() for s in self.anchors + self.conflicts):
            raise ValueError("Anchors and conflicts must be nonempty")
        return self


class Plan(StrictModel):
    id: str
    title: str
    synthetic: bool
    targets: list[Target] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [t.id for t in self.targets]
        if len(ids) != len(set(ids)):
            raise ValueError("Target IDs must be unique")
        return self


Status = Literal["covered", "missing", "needs_review", "possible_conflict"]


class Evidence(StrictModel):
    quote: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)


class Finding(StrictModel):
    target_id: str
    status: Status
    evidence: list[Evidence]
    reason: str
    question: str


class Barrier(StrictModel):
    category: Literal["transport", "cost", "language", "support"]
    evidence: Evidence
    question: str


class Report(StrictModel):
    plan_id: str
    engine: str
    transcript: str
    findings: list[Finding]
    barriers: list[Barrier]
    warnings: list[str]
    requires_human_review: bool = True


class Segment(StrictModel):
    start: float
    end: float
    text: str
    avg_logprob: float
    no_speech_prob: float


class Transcription(StrictModel):
    text: str
    model: str
    language: str
    duration_seconds: float
    elapsed_seconds: float
    segments: list[Segment]
    warnings: list[str]
