"""Demo script: shows PawPal+ planning, conflict warnings, recurring tasks, and filtering.

Run it with:  python main.py
"""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task

WIDTH = 64


def heading(title: str) -> None:
    """Print a section title with a line under it."""
    print(f"\n{title}")
    print("-" * WIDTH)


def print_tasks(tasks: list[Task], show_date: bool = False) -> None:
    """Print tasks as a simple table, one row per task."""
    if not tasks:
        print("(none)")
    for t in tasks:
        day = f"{t.due_date:%a %b %d}  " if show_date else ""
        done = "done" if t.completed else ""
        row = f"{day}{t.time}-{t.end_time()}  {t.description:<18} {t.pet_name:<6} {t.priority:<7} {done}"
        print(row.rstrip())


def build_demo_owner() -> Owner:
    """Create the sample owner, pets, and tasks (also used by the app's "Load sample data" button)."""
    owner = Owner("Jordan", available_minutes=90)
    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added out of order on purpose, so you can see the scheduler sort them.
    mochi.add_task(Task("Fetch in the yard", "17:00", 45, priority="low"))
    luna.add_task(Task("Brush coat", "19:00", 15, priority="medium"))
    mochi.add_task(Task("Morning walk", "07:30", 30, priority="high", frequency="daily"))
    luna.add_task(Task("Flea medicine", "09:00", 5, priority="medium", frequency="weekly"))
    mochi.add_task(Task("Breakfast", "08:00", 10, priority="high", frequency="daily"))
    luna.add_task(Task("Breakfast", "08:15", 5, priority="high", frequency="daily"))
    luna.add_task(Task("Call the vet", "07:30", 15, priority="high"))  # same time as the walk
    return owner


def main() -> None:
    """Build sample data and walk through each feature."""
    owner = build_demo_owner()
    scheduler = Scheduler(owner)

    # 1. Build today's plan: pick by priority, then sort by time.
    plan = scheduler.build_daily_plan()
    heading(f"Today's Schedule for {owner.name} ({date.today():%A, %B %d})")
    print_tasks(plan)
    print("-" * WIDTH)
    print(scheduler.explain_plan(plan))

    # 2. Check the plan for overlapping tasks.
    heading("Conflict check")
    conflicts = scheduler.detect_conflicts(plan)
    for warning in conflicts:
        print(f"WARNING: {warning}")
    if not conflicts:
        print("No conflicts.")

    # 3. Finish a few tasks. Repeating ones come back on their next due date.
    heading("Recurring tasks")
    for name in ("Morning walk", "Flea medicine", "Call the vet"):
        task = next(t for t in owner.get_all_tasks() if t.description == name)
        next_task = scheduler.complete_task(task)
        result = (
            f"next one added for {next_task.due_date:%a %b %d}"
            if next_task
            else "doesn't repeat, nothing added"
        )
        print(f"Done: {task.description} ({task.pet_name}, {task.frequency}) -> {result}")

    # 4. Filter by pet and by status.
    heading("Filter: Mochi's tasks")
    print_tasks(scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Mochi")), show_date=True)

    heading("Filter: finished tasks")
    print_tasks(scheduler.sort_by_time(scheduler.filter_tasks(completed=True)), show_date=True)


if __name__ == "__main__":
    main()
