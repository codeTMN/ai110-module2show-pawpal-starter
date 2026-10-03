"""PawPal+ logic layer.

All the backend classes live here: Task, Pet, Owner, and Scheduler.
The Streamlit app (app.py) and the demo script should only talk to these classes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Task:
    """One pet care activity, like a walk, a feeding, or a vet visit."""

    description: str
    time: str  # start time as "HH:MM" (24-hour)
    duration_minutes: int
    priority: str = "medium"  # "low", "medium", or "high"
    frequency: str = "once"  # "once", "daily", or "weekly"
    due_date: date = field(default_factory=date.today)
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass

    def next_occurrence(self) -> Task | None:
        """Return a fresh copy of this task for its next due date, or None if it only happens once."""
        pass

    def end_time(self) -> str:
        """Return when this task finishes as "HH:MM", based on its start time and duration."""
        pass


@dataclass
class Pet:
    """A pet and the care tasks that belong to it."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet."""
        pass

    def remove_task(self, description: str) -> None:
        """Remove the task with this description."""
        pass

    def get_pending_tasks(self) -> list[Task]:
        """Return the tasks that aren't done yet."""
        pass


@dataclass
class Owner:
    """A pet owner, their daily time budget, and their pets."""

    name: str
    available_minutes: int = 120  # time they can spend on pet care per day
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def remove_pet(self, name: str) -> None:
        """Remove the pet with this name."""
        pass

    def get_pet(self, name: str) -> Pet | None:
        """Find a pet by name, or return None if there isn't one."""
        pass

    def get_all_tasks(self) -> list[Task]:
        """Return every task from every pet in one list."""
        pass


class Scheduler:
    """The brain of PawPal+. Reads tasks from an Owner and turns them into a daily plan."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def build_daily_plan(self, day: date | None = None) -> list[Task]:
        """Pick and order the tasks due on `day` (today by default) that fit in the owner's time.

        Higher priority tasks get picked first.
        """
        pass

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by start time, earliest first."""
        pass

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by priority, highest first."""
        pass

    def filter_tasks(self, pet_name: str | None = None, completed: bool | None = None) -> list[Task]:
        """Return the owner's tasks, narrowed down to one pet and/or a done/not-done status."""
        pass

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Return a warning message for each pair of tasks whose time slots overlap."""
        pass

    def complete_task(self, pet: Pet, task: Task) -> None:
        """Mark a task done. If it repeats, add the next one to the pet."""
        pass

    def explain_plan(self, plan: list[Task]) -> str:
        """Return a short, readable explanation of why the plan looks the way it does."""
        pass
