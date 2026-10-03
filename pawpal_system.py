"""PawPal+ logic layer.

All the backend classes live here: Task, Pet, Owner, and Scheduler.
The Streamlit app (app.py) and the demo script should only talk to these classes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}
FREQUENCIES = ("once", "daily", "weekly")


def _to_minutes(hhmm: str) -> int:
    """Turn an "HH:MM" string into minutes after midnight."""
    try:
        hours, minutes = (int(part) for part in hhmm.split(":"))
    except ValueError:
        raise ValueError(f"Time must look like HH:MM, for example 08:30 (got {hhmm!r}).") from None
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        raise ValueError(f"Time must be between 00:00 and 23:59 (got {hhmm!r}).")
    return hours * 60 + minutes


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
    pet_name: str = ""  # filled in by Pet.add_task()

    def __post_init__(self) -> None:
        """Catch bad values early so they don't cause weird sorting later."""
        if self.priority not in PRIORITY_RANK:
            raise ValueError(f"Priority must be low, medium, or high (got {self.priority!r}).")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"Frequency must be once, daily, or weekly (got {self.frequency!r}).")
        if self.duration_minutes <= 0:
            raise ValueError("Duration must be at least 1 minute.")
        start = _to_minutes(self.time)  # raises ValueError if the time isn't "HH:MM"
        self.time = f"{start // 60:02d}:{start % 60:02d}"  # store "8:05" as "08:05"

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def next_occurrence(self) -> Task | None:
        """Return a fresh copy of this task for its next due date, or None if it only happens once."""
        raise NotImplementedError("Recurring tasks are coming in Phase 4.")

    def end_time(self) -> str:
        """Return when this task finishes as "HH:MM", based on its start time and duration."""
        total = _to_minutes(self.time) + self.duration_minutes
        return f"{total // 60 % 24:02d}:{total % 60:02d}"

    def priority_rank(self) -> int:
        """Return priority as a number (high = 3) so tasks sort in the right order."""
        return PRIORITY_RANK[self.priority]


@dataclass
class Pet:
    """A pet and the care tasks that belong to it."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet and tag it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove this exact task from the pet."""
        self.tasks = [t for t in self.tasks if t is not task]

    def get_pending_tasks(self) -> list[Task]:
        """Return the tasks that aren't done yet."""
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    """A pet owner, their daily time budget, and their pets."""

    name: str
    available_minutes: int = 120  # time they can spend on pet care per day
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner. Pet names must be unique since tasks find their pet by name."""
        if self.get_pet(pet.name) is not None:
            raise ValueError(f"{self.name} already has a pet named {pet.name}.")
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        """Remove the pet with this name."""
        self.pets = [p for p in self.pets if p.name != name]

    def get_pet(self, name: str) -> Pet | None:
        """Find a pet by name, or return None if there isn't one."""
        return next((p for p in self.pets if p.name == name), None)

    def get_all_tasks(self) -> list[Task]:
        """Return every task from every pet in one list."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """The brain of PawPal+. Reads tasks from an Owner and turns them into a daily plan."""

    def __init__(self, owner: Owner) -> None:
        """Hook the scheduler up to an owner so it can see all of their pets' tasks."""
        self.owner = owner
        self.skipped: list[Task] = []  # tasks left out of the last plan because time ran out

    def build_daily_plan(self, day: date | None = None) -> list[Task]:
        """Pick and order the tasks due on `day` (today by default) that fit in the owner's time.

        Higher priority tasks get picked first. Anything that doesn't fit goes in self.skipped.
        """
        day = day or date.today()
        due_today = [
            t for t in self.owner.get_all_tasks() if t.due_date == day and not t.completed
        ]

        plan: list[Task] = []
        self.skipped = []
        minutes_left = self.owner.available_minutes
        for task in self.sort_by_priority(due_today):
            if task.duration_minutes <= minutes_left:
                plan.append(task)
                minutes_left -= task.duration_minutes
            else:
                self.skipped.append(task)

        return self.sort_by_time(plan)

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by start time, earliest first."""
        return sorted(tasks, key=lambda t: _to_minutes(t.time))

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by priority, highest first. Ties go to the earlier task."""
        return sorted(tasks, key=lambda t: (-t.priority_rank(), _to_minutes(t.time)))

    def filter_tasks(self, pet_name: str | None = None, completed: bool | None = None) -> list[Task]:
        """Return the owner's tasks, narrowed down to one pet and/or a done/not-done status."""
        raise NotImplementedError("Filtering is coming in Phase 4.")

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Return a warning message for each pair of tasks whose time slots overlap."""
        raise NotImplementedError("Conflict detection is coming in Phase 4.")

    def complete_task(self, task: Task) -> Task | None:
        """Mark a task done. If it repeats, add the next one to the same pet and return it."""
        raise NotImplementedError("Recurring tasks are coming in Phase 4.")

    def explain_plan(self, plan: list[Task]) -> str:
        """Return a short, readable explanation of why the plan looks the way it does."""
        if not plan and not self.skipped:
            return "Nothing is due today."

        used = sum(t.duration_minutes for t in plan)
        lines = [
            f"Planned {len(plan)} task(s) using {used} of {self.owner.available_minutes} available minutes.",
            "Higher-priority tasks were picked first, then the plan was put in time order.",
        ]
        for t in self.skipped:
            lines.append(
                f"Skipped: {t.description} for {t.pet_name} "
                f"({t.duration_minutes} min, {t.priority} priority), not enough time left."
            )
        return "\n".join(lines)
