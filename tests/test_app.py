from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_review_flow():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
    assert not app.exception
    next(b for b in app.button if b.label == "Review teach-back").click().run()
    assert not app.exception
    assert len(app.metric) == 4
    assert app.metric[0].value == "3"
    app.text_area[0].set_value("I am unsure.").run()
    assert len(app.metric) == 0  # Never show a stale report after transcript edits.
    next(b for b in app.button if b.label == "Review teach-back").click().run()
    assert app.metric[3].value == "3"
