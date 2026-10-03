"""End-to-end checks of the Streamlit app, using Streamlit's built-in AppTest runner.

Each test points the app at its own throwaway data file, so it never touches data.json.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


@pytest.fixture
def app(tmp_path, monkeypatch):
    """A fresh app session with the sample data loaded."""
    monkeypatch.setenv("PAWPAL_DATA_FILE", str(tmp_path / "data.json"))
    at = AppTest.from_file(APP, default_timeout=60).run()
    click(at, "Load sample data")
    return at


def click(at, label_start):
    """Click the first button whose label starts with this text, then rerun the app."""
    next(b for b in at.button if b.label.startswith(label_start)).click()
    at.run()
    assert not at.exception, at.exception


def element_types(at):
    """Every element type on the main page, including nested ones."""
    found, stack = [], list(at.main.children.values())
    while stack:
        node = stack.pop()
        found.append(getattr(node, "type", ""))
        stack.extend(getattr(node, "children", {}).values())
    return found


def test_sample_data_shows_clash_and_one_click_fix(app):
    assert len(app.warning) == 1
    assert "next free time for Call the vet is 08:20" in app.warning[0].value

    click(app, "Move Call the vet")

    assert len(app.warning) == 0
    vet = next(t for t in app.session_state.owner.get_all_tasks() if t.description == "Call the vet")
    assert vet.time == "08:20"


def test_mark_done_shows_message_without_stray_output(app):
    # Regression test: a one-line "st.error(...) if ... else st.success(...)" used to make
    # Streamlit print the return value's help text under the message.
    click(app, "Mark done")

    assert "is done" in app.success[0].value
    assert "help_info" not in element_types(app)


def test_data_survives_a_restart(app, tmp_path):
    click(app, "Mark done")

    restarted = AppTest.from_file(APP, default_timeout=60).run()

    assert restarted.session_state.owner == app.session_state.owner
    assert (tmp_path / "data.json").exists()
