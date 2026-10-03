"""PawPal+ logic layer.

All the backend classes live here: Task, Pet, Owner, and Scheduler.
The Streamlit app (app.py) and the demo script should only talk to these classes.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from datetime import date, timedelta
from itertools import combinations
from pathlib import Path

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


def _from_minutes(total: int) -> str:
    """Turn minutes after midnight back into an "HH:MM" string."""
    return f"{total // 60 % 24:02d}:{total % 60:02d}"


def _overlaps(a: Task, b: Task) -> bool:
    """True if two tasks on the same day overlap. Back-to-back tasks don't count."""
    a_start, b_start = _to_minutes(a.time), _to_minutes(b.time)
    return (
        a.due_date == b.due_date
        and a_start < b_start + b.duration_minutes
        and b_start < a_start + a.duration_minutes
    )


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
        self.time = _from_minutes(start)  # store "8:05" as "08:05"

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def next_occurrence(self) -> Task | None:
        """Return a fresh copy of this task for its next due date, or None if it only happens once.

        Counts from today or the old due date, whichever is later, so a task that gets
        finished late doesn't come back with a date that has already passed.
        """
        if self.frequency == "once":
            return None
        step = timedelta(days=1) if self.frequency == "daily" else timedelta(weeks=1)
        start_from = max(self.due_date, date.today())
        return replace(self, due_date=start_from + step, completed=False)

    def end_time(self) -> str:
        """Return when this task finishes as "HH:MM", based on its start time and duration."""
        return _from_minutes(_to_minutes(self.time) + self.duration_minutes)

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

    def save_to_json(self, path: str | Path) -> None:
        """Save this owner, their pets, and all their tasks to a JSON file.

        asdict() turns the nested dataclasses into plain dicts and lists, and dates are
        written as "YYYY-MM-DD" text. The file is written to a temp file first and then
        swapped in, so a crash mid-save can't leave a half-written data file behind.
        """
        path = Path(path)
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(asdict(self), indent=2, default=str))
        temp.replace(path)

    @classmethod
    def load_from_json(cls, path: str | Path) -> Owner:
        """Rebuild an owner, with pets and tasks, from a file made by save_to_json().

        Tasks are rebuilt through the normal Task constructor, so a hand-edited file with
        a bad value (like a 25:00 start time) raises ValueError instead of sneaking in.
        """
        data = json.loads(Path(path).read_text())
        owner = cls(name=data["name"], available_minutes=data["available_minutes"])
        for pet_data in data["pets"]:
            pet = Pet(pet_data["name"], pet_data["species"], pet_data["age"])
            for task_data in pet_data["tasks"]:
                pet.add_task(Task(**{**task_data, "due_date": date.fromisoformat(task_data["due_date"])}))
            owner.add_pet(pet)
        return owner


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
        """Return tasks in the order they happen: by due date, then by start time.

        Comparing the "HH:MM" strings directly is safe because Task always stores
        times zero-padded ("08:05", never "8:05").
        """
        return sorted(tasks, key=lambda t: (t.due_date, t.time))

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by priority, highest first. Ties go to the earlier task."""
        return sorted(tasks, key=lambda t: (-t.priority_rank(), t.time))

    def filter_tasks(self, pet_name: str | None = None, completed: bool | None = None) -> list[Task]:
        """Return the owner's tasks, narrowed down to one pet and/or a done/not-done status.

        Leave an argument as None to skip that filter.
        """
        tasks = self.owner.get_all_tasks()
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet_name == pet_name]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        return tasks

    def find_conflicting_pairs(self, tasks: list[Task]) -> list[tuple[Task, Task]]:
        """Return every pair of tasks on the same day whose time slots overlap, earlier task first.

        Checks every pair on purpose. Comparing only neighbors in time order is shorter,
        but it misses a long task that runs into two later ones.
        """
        return [(a, b) for a, b in combinations(self.sort_by_time(tasks), 2) if _overlaps(a, b)]

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Return a warning message for each pair of tasks on the same day whose time slots overlap.

        Two tasks overlap when each one starts before the other one ends, so a walk from
        07:30 to 08:00 and breakfast at 08:00 don't clash. This only reports problems;
        it never raises and never moves tasks, so the owner decides what to change.
        """
        return [
            f"{a.pet_name}'s {a.description} ({a.time}-{a.end_time()}) overlaps with "
            f"{b.pet_name}'s {b.description} ({b.time}-{b.end_time()})."
            for a, b in self.find_conflicting_pairs(tasks)
        ]

    def find_next_slot(
        self,
        duration_minutes: int,
        day: date | None = None,
        earliest: str = "06:00",
        latest: str = "22:00",
        ignore: Task | None = None,
    ) -> str | None:
        """Return the earliest "HH:MM" start time on `day` where a task this long fits.

        Walks through the day's unfinished tasks in time order, keeping track of when the
        last busy stretch ends. The first gap that's long enough wins. Returns None if
        nothing fits between `earliest` and `latest`. Pass `ignore` to leave out the task
        you're trying to move, so it doesn't block itself.
        """
        day = day or date.today()
        busy = [
            t for t in self.owner.get_all_tasks()
            if t.due_date == day and not t.completed and t is not ignore
        ]
        candidate = _to_minutes(earliest)
        for task in self.sort_by_time(busy):
            start = _to_minutes(task.time)
            if candidate + duration_minutes <= start:
                break  # the gap before this task is big enough
            candidate = max(candidate, start + task.duration_minutes)
        if candidate + duration_minutes > _to_minutes(latest):
            return None
        return _from_minutes(candidate)

    def suggest_move(self, a: Task, b: Task) -> tuple[Task, str] | None:
        """For two clashing tasks, suggest which one to move and the next free time for it.

        Moves the lower-priority task (or the later one if they tie), and only looks for
        times after its current start, since owners usually plan around a task's time.
        Returns None if there's no free slot left that day.
        """
        to_move = a if a.priority_rank() < b.priority_rank() else b
        slot = self.find_next_slot(
            to_move.duration_minutes, day=to_move.due_date, earliest=to_move.time, ignore=to_move
        )
        return (to_move, slot) if slot else None

    def complete_task(self, task: Task) -> Task | None:
        """Mark a task done. If it repeats, add the next one to the same pet and return it.

        Calling this on a task that's already done does nothing, so a double click
        can't create two copies of tomorrow's task.
        """
        if task.completed:
            return None
        task.mark_complete()
        next_task = task.next_occurrence()
        pet = self.owner.get_pet(task.pet_name)
        if next_task is not None and pet is not None:
            pet.add_task(next_task)
        return next_task

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
