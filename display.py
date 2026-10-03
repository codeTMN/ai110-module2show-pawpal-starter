"""Display helpers shared by the app and the demo script: task emojis and status badges.

Kept out of pawpal_system.py on purpose, so the logic layer has no opinions about looks.
"""

import re

from pawpal_system import Task

PRIORITY_BADGES = {"high": "🔴 high", "medium": "🟡 medium", "low": "🟢 low"}

# Checked in order, and the first group with a matching word wins, so "Call the vet"
# gets the vet emoji even though "call" isn't a walk or a meal. A word matches when it
# starts with a keyword, so "meds" and "medicine" both match "med", but "brunch"
# doesn't match "run".
TASK_EMOJIS = [
    (("vet", "doctor", "checkup"), "🩺"),
    (("med", "pill", "flea", "vaccine", "dose"), "💊"),
    (("walk", "hike", "run", "jog"), "🦮"),
    (("breakfast", "brunch", "lunch", "dinner", "feed", "meal", "food", "treat"), "🍖"),
    (("brush", "groom", "bath", "nail", "comb"), "🛁"),
    (("play", "fetch", "toy", "train"), "🎾"),
]
DEFAULT_EMOJI = "🐾"


def task_emoji(task: Task) -> str:
    """Pick an emoji for a task based on the words in its description."""
    words = re.findall(r"[a-z]+", task.description.lower())
    for keywords, emoji in TASK_EMOJIS:
        if any(word.startswith(keyword) for word in words for keyword in keywords):
            return emoji
    return DEFAULT_EMOJI


def task_label(task: Task) -> str:
    """Task description with its emoji in front, like "🦮 Morning walk"."""
    return f"{task_emoji(task)} {task.description}"


def priority_badge(priority: str) -> str:
    """Color-coded priority, like "🔴 high"."""
    return PRIORITY_BADGES[priority]


def status_badge(task: Task) -> str:
    """"✅ done" or "⏳ to do"."""
    return "✅ done" if task.completed else "⏳ to do"
