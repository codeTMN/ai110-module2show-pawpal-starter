"""Demo script: sets up an owner with two pets and prints today's schedule.

Run it with:  python main.py
"""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(scheduler: Scheduler, plan: list[Task]) -> None:
    """Print the plan as a simple table, followed by the explanation."""
    today = date.today().strftime("%A, %B %d")
    print(f"Today's Schedule for {scheduler.owner.name} ({today})")
    print("=" * 56)
    print(f"{'Time':<12} {'Task':<20} {'Pet':<7} Priority")
    print("-" * 56)
    for task in plan:
        print(f"{task.time}-{task.end_time()}  {task.description:<20} {task.pet_name:<7} {task.priority}")
    print("-" * 56)
    print(scheduler.explain_plan(plan))


def main() -> None:
    """Build sample data and show the schedule."""
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

    scheduler = Scheduler(owner)
    plan = scheduler.build_daily_plan()
    print_schedule(scheduler, plan)


if __name__ == "__main__":
    main()
