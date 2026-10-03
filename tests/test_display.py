import pytest

from display import priority_badge, status_badge, task_emoji, task_label
from pawpal_system import Task


@pytest.mark.parametrize(
    "description, emoji",
    [
        ("Morning walk", "🦮"),
        ("Breakfast", "🍖"),
        ("Flea medicine", "💊"),
        ("Call the vet", "🩺"),  # vet wins even though other words are present
        ("Brush coat", "🛁"),
        ("Fetch in the yard", "🎾"),
        ("Sunday brunch", "🍖"),  # "brunch" contains "run" but must not count as a walk
        ("Clean litter box", "🐾"),  # no keyword, falls back to the paw
    ],
)
def test_task_emoji_matches_on_words(description, emoji):
    assert task_emoji(Task(description, "08:00", 10)) == emoji


def test_labels_and_badges():
    task = Task("Morning walk", "07:30", 30, priority="high")
    assert task_label(task) == "🦮 Morning walk"
    assert priority_badge("high") == "🔴 high"
    assert status_badge(task) == "⏳ to do"
    task.mark_complete()
    assert status_badge(task) == "✅ done"
