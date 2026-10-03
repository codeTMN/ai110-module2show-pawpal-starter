"""Demo script: shows PawPal+ planning, priority order, conflict warnings with a suggested
fix, the next free slot, recurring tasks, and filtering.

Run it with:  python main.py
"""

from datetime import date

from tabulate import tabulate

from display import priority_badge, status_badge, task_label
from pawpal_system import Owner, Pet, Scheduler, Task


def heading(title: str) -> None:
    """Print a section title with a line under it."""
    print(f"\n{title}")
    print("=" * len(title))


def print_tasks(tasks: list[Task], show_date: bool = False) -> None:
    """Print tasks as a table with emojis, color-coded priority, and status."""
    if not tasks:
        print("(none)")
        return
    rows = [
        ([f"{t.due_date:%a %b %d}"] if show_date else [])
        + [f"{t.time}-{t.end_time()}", task_label(t), t.pet_name, priority_badge(t.priority), status_badge(t)]
        for t in tasks
    ]
    headers = (["Date"] if show_date else []) + ["Time", "Task", "Pet", "Priority", "Status"]
    print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))


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
    mochi.add_task(Task("Dinner", "18:00", 10, priority="high", frequency="daily"))
    return owner


def main() -> None:
    """Build sample data and walk through each feature."""
    owner = build_demo_owner()
    scheduler = Scheduler(owner)

    # 1. Build today's plan: pick by priority, then sort by time.
    plan = scheduler.build_daily_plan()
    heading(f"Today's Schedule for {owner.name} ({date.today():%A, %B %d})")
    print_tasks(plan)
    print(scheduler.explain_plan(plan))

    # 2. All of today's tasks in priority order (ties broken by start time). This is
    #    the order build_daily_plan() picks them in, so it shows why Fetch was skipped.
    heading("All of today's tasks, by priority then time")
    print_tasks(scheduler.sort_by_priority(scheduler.filter_tasks(completed=False)))

    # 3. Check the plan for overlapping tasks and suggest a fix.
    heading("Conflict check")
    pairs = scheduler.find_conflicting_pairs(plan)
    for (a, b), warning in zip(pairs, scheduler.detect_conflicts(plan)):
        print(f"⚠️  WARNING: {warning}")
        suggestion = scheduler.suggest_move(a, b)
        if suggestion:
            task, new_time = suggestion
            print(f"   Suggestion: move {task.pet_name}'s {task.description} to {new_time}, the next free time.")
    if not pairs:
        print("No conflicts.")

    # 4. Find the next open time for a new task.
    heading("Next free slot after 07:30")
    for minutes in (20, 60):
        print(f"A {minutes}-minute task fits at: {scheduler.find_next_slot(minutes, earliest='07:30')}")

    # 5. Finish a few tasks. Repeating ones come back on their next due date.
    heading("Recurring tasks")
    for name in ("Morning walk", "Flea medicine", "Call the vet"):
        task = next(t for t in owner.get_all_tasks() if t.description == name)
        next_task = scheduler.complete_task(task)
        result = (
            f"next one added for {next_task.due_date:%a %b %d}"
            if next_task
            else "doesn't repeat, nothing added"
        )
        print(f"✅ {task.description} ({task.pet_name}, {task.frequency}) -> {result}")

    # 6. Filter by pet and by status.
    heading("Filter: Mochi's tasks")
    print_tasks(scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Mochi")), show_date=True)

    heading("Filter: finished tasks")
    print_tasks(scheduler.sort_by_time(scheduler.filter_tasks(completed=True)), show_date=True)


if __name__ == "__main__":
    main()
