"""Local reviewer workbench. No database, telemetry, or automatic API calls."""

import json
import tempfile
from pathlib import Path

import streamlit as st

from careecho.audio import inspect_wav, transcribe
from careecho.nlp import review
from careecho.schema import Plan

ROOT = Path(__file__).parent
st.set_page_config(page_title="CareEcho | Teach-back workbench", page_icon="🌱", layout="wide")
st.markdown(
    """<style>
.stApp {background: #f7f9f8;}
h1, h2, h3 {color: #123e36;}
[data-testid="stMetric"] {background: white; padding: 14px; border-radius: 12px; border: 1px solid #dce8e2;}
</style>""",
    unsafe_allow_html=True,
)
st.caption("CAREECHO  /  HEALTH LITERACY RESEARCH")
st.title("A clearer path from hospital to home.")
st.write(
    "Review what a patient explains back, find details to revisit, and surface barriers to care."
)
st.warning(
    "Synthetic-data research demo. Findings need human review and must not guide patient care."
)

cases = json.loads((ROOT / "data/cases.json").read_text(encoding="utf-8"))
with st.sidebar:
    st.header("Review workspace")
    case_id = st.selectbox("Synthetic scenario", [c["id"] for c in cases])
    case = next(c for c in cases if c["id"] == case_id)
    engine = st.radio("Review engine", ["Local phrase baseline", "OpenAI structured review"])
    model = st.text_input("API model (or OPENAI_MODEL)") if engine.startswith("OpenAI") else None
    consent = (
        st.checkbox(
            "I confirm this is synthetic text and consent to sending the plan and transcript to OpenAI."
        )
        if model is not None
        else False
    )
    st.caption(
        "Local analysis needs no API key. Audio uses CPU Whisper; first use downloads model weights from Hugging Face."
    )

plan = Plan.model_validate_json(
    (ROOT / f"data/plans/{case['plan']}.json").read_text(encoding="utf-8")
)
left, right = st.columns([1, 1.35], gap="large")
with left:
    st.subheader("1 · Reference plan")
    st.caption(plan.title)
    for target in plan.targets:
        with st.container(border=True):
            st.caption(target.category.replace("_", " ").upper())
            st.write(target.instruction)
    with st.expander("Inspect structured targets"):
        st.json(plan.model_dump())

with right:
    st.subheader("2 · Patient teach-back")
    if st.session_state.get("case_id") != case_id:
        st.session_state.case_id = case_id
        st.session_state.transcript = case["transcript"]
        st.session_state.pop("report", None)
        st.session_state.pop("report_signature", None)
    with st.expander("Transcribe synthetic audio locally"):
        upload = st.file_uploader("16-bit PCM WAV · up to 3 minutes / 25 MB", type=["wav"])
        asr_model = st.selectbox("Whisper model", ["tiny.en", "base.en", "small.en"])
        glossary = st.text_input(
            "Optional vocabulary hint", placeholder="Use terms only, not a desired answer"
        )
        if st.button("Run local speech recognition", disabled=upload is None):
            temp_path = None
            try:
                if upload.size > 25 * 1024 * 1024:
                    raise ValueError("Audio exceeds 25 MB")
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
                    temp.write(upload.getvalue())
                    temp_path = Path(temp.name)
                st.json(inspect_wav(temp_path))
                with st.spinner("Transcribing on CPU…"):
                    result = transcribe(temp_path, asr_model, glossary)
                st.session_state.transcript = result.text
                st.json(result.model_dump())
            except Exception:
                st.error(
                    "Audio processing failed. Check the WAV format, ASR installation, and model download access. No cloud review was run."
                )
            finally:
                if temp_path:
                    temp_path.unlink(missing_ok=True)
    transcript = st.text_area(
        "Editable transcript — check against the recording", key="transcript", height=210
    )
    st.caption(
        "Edits change the evidence being reviewed. No transcript is automatically persisted."
    )
    if st.button("Review teach-back", type="primary"):
        st.session_state.pop("report", None)
        try:
            with st.spinner("Reviewing evidence…"):
                if engine.startswith("OpenAI"):
                    from careecho.llm import review_with_llm

                    report = review_with_llm(plan, transcript, consent=consent, model=model or None)
                else:
                    report = review(plan, transcript)
            st.session_state.report = report.model_dump()
            st.session_state.report_signature = (case_id, transcript, engine, model)
        except Exception:
            st.error(
                "Review failed. For cloud review, check synthetic-data consent, OPENAI_API_KEY, and a supported model. Invalid model responses are rejected."
            )

if "report" in st.session_state and st.session_state.get("report_signature") == (
    case_id,
    transcript,
    engine,
    model,
):
    report = st.session_state.report
    st.divider()
    st.subheader("3 · Human review queue")
    counts = {
        s: sum(f["status"] == s for f in report["findings"])
        for s in ["covered", "needs_review", "possible_conflict", "missing"]
    }
    for col, (label, value) in zip(st.columns(4), counts.items()):
        col.metric(label.replace("_", " ").title(), value)
    st.caption(
        "These counts describe matching evidence, not patient comprehension or readiness for discharge."
    )
    targets = {t.id: t for t in plan.targets}
    for finding in report["findings"]:
        with st.container(border=True):
            st.markdown(
                f"**{finding['status'].replace('_', ' ').upper()} · {targets[finding['target_id']].category.replace('_', ' ')}**"
            )
            st.write(targets[finding["target_id"]].instruction)
            for evidence in finding["evidence"]:
                st.text(
                    f"“{evidence['quote']}”  [characters {evidence['start']}:{evidence['end']}]"
                )
            st.caption(finding["reason"])
            if finding["status"] != "covered":
                st.info(f"Ask next: {finding['question']}")
    st.subheader("Access and support")
    if not report["barriers"]:
        st.write(
            "No configured barrier phrase found. This does not establish that no barriers exist."
        )
    for barrier in report["barriers"]:
        st.warning(f"{barrier['category'].title()}: {barrier['question']}")
        st.text(barrier["evidence"]["quote"])
    with st.expander("Audit report and limitations"):
        st.json(report)
    st.download_button(
        "Download review JSON",
        json.dumps(report, indent=2),
        "careecho-review.json",
        "application/json",
    )
