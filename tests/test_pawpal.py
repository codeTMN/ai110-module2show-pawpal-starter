from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task

TODAY = date.today()
ONE_DAY = timedelta(days=1)


@pytest.fixture
def owner():
    """An owner with two pets and no tasks yet."""
    owner = Owner("Jordan", available_minutes=60)
    owner.add_pet(Pet("Mochi", "dog"))
    owner.add_pet(Pet("Luna", "cat"))
    return owner


@pytest.fixture
def scheduler(owner):
    """A scheduler hooked up to the owner fixture."""
    return Scheduler(owner)


# --- Task and Pet basics -------------------------------------------------------


def test_mark_complete_changes_status():
    task = Task("Morning walk", "07:30", 30)
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Breakfast", "08:00", 10))

    assert len(pet.tasks) == 1
    assert pet.tasks[0].pet_name == "Mochi"


def test_end_time_adds_duration_to_start():
    assert Task("Walk", "07:45", 30).end_time() == "08:15"


def test_short_times_are_stored_zero_padded():
    assert Task("Walk", "8:05", 10).time == "08:05"


@pytest.mark.parametrize(
    "bad_args",
    [
        {"priority": "urgent"},
        {"frequency": "monthly"},
        {"time": "8am"},
        {"time": "25:00"},
        {"duration_minutes": 0},
    ],
)
def test_bad_task_values_are_rejected(bad_args):
    args = {"description": "Walk", "time": "08:00", "duration_minutes": 10} | bad_args
    with pytest.raises(ValueError):
        Task(**args)


def test_owner_cannot_have_two_pets_with_the_same_name(owner):
    with pytest.raises(ValueError):
        owner.add_pet(Pet("Mochi", "cat"))


def test_remove_task_removes_only_that_exact_task():
    pet = Pet("Mochi", "dog")
    morning = Task("Feeding", "08:00", 10)
    evening = Task("Feeding", "08:00", 10)  # same details, different task
    pet.add_task(morning)
    pet.add_task(evening)

    pet.remove_task(evening)

    assert len(pet.tasks) == 1
    assert pet.tasks[0] is morning


# --- Sorting -------------------------------------------------------------------


def test_sort_by_time_returns_tasks_in_chronological_order(scheduler):
    tasks = [Task("Dinner", "18:00", 10), Task("Walk", "07:30", 30), Task("Meds", "12:15", 5)]

    result = scheduler.sort_by_time(tasks)

    assert [t.time for t in result] == ["07:30", "12:15", "18:00"]


def test_sort_by_time_puts_earlier_days_first(scheduler):
    tomorrow_early = Task("Walk", "07:00", 30, due_date=TODAY + ONE_DAY)
    today_late = Task("Dinner", "18:00", 10, due_date=TODAY)

    result = scheduler.sort_by_time([tomorrow_early, today_late])

    assert result == [today_late, tomorrow_early]


def test_sort_by_priority_puts_high_first_and_breaks_ties_by_time(scheduler):
    low = Task("Fetch", "06:00", 20, priority="low")
    high_late = Task("Meds", "09:00", 5, priority="high")
    high_early = Task("Walk", "07:00", 30, priority="high")
    medium = Task("Brush", "08:00", 15, priority="medium")

    result = scheduler.sort_by_priority([low, high_late, high_early, medium])

    assert result == [high_early, high_late, medium, low]


# --- Building the daily plan ---------------------------------------------------


def test_plan_fits_in_available_time_and_skips_lower_priority(owner, scheduler):
    mochi = owner.get_pet("Mochi")
    walk = Task("Walk", "07:30", 30, priority="high")
    meds = Task("Meds", "09:00", 10, priority="medium")
    fetch = Task("Fetch", "17:00", 45, priority="low")  # won't fit in the last 20 minutes
    for task in (fetch, meds, walk):
        mochi.add_task(task)

    plan = scheduler.build_daily_plan()

    assert plan == [walk, meds]  # chosen by priority, shown in time order
    assert scheduler.skipped == [fetch]
    assert "Skipped: Fetch" in scheduler.explain_plan(plan)


def test_plan_ignores_finished_tasks_and_other_days(owner, scheduler):
    mochi = owner.get_pet("Mochi")
    done = Task("Walk", "07:30", 30)
    done.mark_complete()
    mochi.add_task(done)
    mochi.add_task(Task("Vet", "10:00", 30, due_date=TODAY + ONE_DAY))
    breakfast = Task("Breakfast", "08:00", 10)
    mochi.add_task(breakfast)

    assert scheduler.build_daily_plan() == [breakfast]


def test_pet_with_no_tasks_gives_an_empty_plan(scheduler):
    plan = scheduler.build_daily_plan()

    assert plan == []
    assert scheduler.skipped == []
    assert scheduler.explain_plan(plan) == "Nothing is due today."


# --- Filtering -----------------------------------------------------------------


def test_filter_by_pet_and_by_status(owner, scheduler):
    walk = Task("Walk", "07:30", 30)
    owner.get_pet("Mochi").add_task(walk)
    owner.get_pet("Luna").add_task(Task("Brush", "19:00", 15))
    walk.mark_complete()

    assert [t.pet_name for t in scheduler.filter_tasks(pet_name="Luna")] == ["Luna"]
    assert scheduler.filter_tasks(completed=True) == [walk]
    assert scheduler.filter_tasks(pet_name="Mochi", completed=False) == []
    assert scheduler.filter_tasks(pet_name="Rex") == []
    assert len(scheduler.filter_tasks()) == 2


# --- Recurring tasks -----------------------------------------------------------


def test_completing_daily_task_creates_one_for_the_next_day(owner, scheduler):
    mochi = owner.get_pet("Mochi")
    walk = Task("Walk", "07:30", 30, frequency="daily")
    mochi.add_task(walk)

    next_walk = scheduler.complete_task(walk)

    assert walk.completed is True
    assert next_walk.due_date == TODAY + ONE_DAY
    assert next_walk.completed is False
    assert next_walk.time == "07:30"
    assert next_walk in mochi.tasks
    assert len(mochi.tasks) == 2


def test_completing_weekly_task_creates_one_for_next_week(owner, scheduler):
    flea = Task("Flea meds", "09:00", 5, frequency="weekly")
    owner.get_pet("Luna").add_task(flea)

    next_flea = scheduler.complete_task(flea)

    assert next_flea.due_date == TODAY + timedelta(weeks=1)


def test_completing_one_time_task_does_not_create_another(owner, scheduler):
    luna = owner.get_pet("Luna")
    vet = Task("Vet", "10:00", 30, frequency="once")
    luna.add_task(vet)

    assert scheduler.complete_task(vet) is None
    assert len(luna.tasks) == 1


def test_completing_same_task_twice_does_not_duplicate(owner, scheduler):
    mochi = owner.get_pet("Mochi")
    walk = Task("Walk", "07:30", 30, frequency="daily")
    mochi.add_task(walk)

    scheduler.complete_task(walk)
    scheduler.complete_task(walk)

    assert len(mochi.tasks) == 2


def test_late_daily_task_comes_back_tomorrow_not_in_the_past():
    overdue = Task("Walk", "07:30", 30, frequency="daily", due_date=TODAY - 3 * ONE_DAY)

    assert overdue.next_occurrence().due_date == TODAY + ONE_DAY


# --- Conflict detection --------------------------------------------------------


def test_tasks_at_the_exact_same_time_are_flagged(owner, scheduler):
    walk = Task("Walk", "07:30", 30)
    call = Task("Vet call", "07:30", 15)
    owner.get_pet("Mochi").add_task(walk)
    owner.get_pet("Luna").add_task(call)

    warnings = scheduler.detect_conflicts([walk, call])

    assert len(warnings) == 1
    assert "Mochi's Walk" in warnings[0] and "Luna's Vet call" in warnings[0]


def test_partly_overlapping_tasks_are_flagged(scheduler):
    walk = Task("Walk", "07:30", 30)  # 07:30-08:00
    meds = Task("Meds", "07:50", 5)  # starts before the walk ends

    assert len(scheduler.detect_conflicts([walk, meds])) == 1


def test_back_to_back_tasks_are_not_flagged(scheduler):
    walk = Task("Walk", "07:30", 30)  # ends at 08:00
    breakfast = Task("Breakfast", "08:00", 10)

    assert scheduler.detect_conflicts([walk, breakfast]) == []


def test_same_time_on_different_days_is_not_flagged(scheduler):
    today = Task("Walk", "07:30", 30, due_date=TODAY)
    tomorrow = Task("Walk", "07:30", 30, due_date=TODAY + ONE_DAY)

    assert scheduler.detect_conflicts([today, tomorrow]) == []


def test_long_task_overlapping_two_later_tasks_flags_both(scheduler):
    # This is the case a "compare neighbors only" shortcut would miss.
    hike = Task("Hike", "08:00", 120)  # 08:00-10:00
    breakfast = Task("Breakfast", "08:30", 10)
    meds = Task("Meds", "09:00", 5)

    warnings = scheduler.detect_conflicts([hike, breakfast, meds])

    assert len(warnings) == 2
    assert any("Meds" in w for w in warnings)


# --- Next available slot (optional extension) -------------------------------------


def test_next_slot_finds_first_gap_that_is_long_enough(owner, scheduler):
    mochi = owner.get_pet("Mochi")
    mochi.add_task(Task("Walk", "06:00", 30))  # 06:00-06:30
    mochi.add_task(Task("Breakfast", "06:40", 10))  # 10-minute gap before this is too short for 20
    mochi.add_task(Task("Meds", "07:30", 5))

    assert scheduler.find_next_slot(20) == "06:50"


def test_next_slot_handles_overlapping_busy_times(owner, scheduler):
    mochi = owner.get_pet("Mochi")
    mochi.add_task(Task("Hike", "06:00", 120))  # 06:00-08:00
    mochi.add_task(Task("Breakfast", "06:30", 10))  # inside the hike, must not reset the clock

    assert scheduler.find_next_slot(15) == "08:00"


def test_next_slot_ignores_done_tasks_and_other_days(owner, scheduler):
    mochi = owner.get_pet("Mochi")
    done = Task("Walk", "06:00", 60)
    done.mark_complete()
    mochi.add_task(done)
    mochi.add_task(Task("Vet", "06:00", 60, due_date=TODAY + ONE_DAY))

    assert scheduler.find_next_slot(30) == "06:00"


def test_next_slot_returns_none_when_the_day_is_full(owner, scheduler):
    owner.get_pet("Mochi").add_task(Task("Long day out", "06:00", 960))  # 06:00-22:00

    assert scheduler.find_next_slot(10) is None


def test_suggest_move_picks_lower_priority_task_and_a_free_time(owner, scheduler):
    walk = Task("Walk", "07:30", 30, priority="high")
    brush = Task("Brush", "07:40", 15, priority="low")
    owner.get_pet("Mochi").add_task(walk)
    owner.get_pet("Luna").add_task(brush)

    (a, b), = scheduler.find_conflicting_pairs([walk, brush])
    to_move, new_time = scheduler.suggest_move(a, b)

    assert to_move is brush
    assert new_time == "08:00"  # right after the walk, not on top of itself


# --- Saving and loading (optional extension) --------------------------------------


def test_save_and_load_round_trip_keeps_everything(owner, tmp_path):
    walk = Task("Walk", "07:30", 30, priority="high", frequency="daily")
    owner.get_pet("Mochi").add_task(walk)
    owner.get_pet("Luna").add_task(Task("Vet", "10:00", 45, due_date=TODAY + ONE_DAY))
    walk.mark_complete()
    path = tmp_path / "data.json"

    owner.save_to_json(path)
    loaded = Owner.load_from_json(path)

    assert loaded == owner  # dataclasses compare every field, including nested pets and tasks
    assert isinstance(loaded.get_pet("Luna").tasks[0].due_date, date)
    assert loaded.get_pet("Mochi").tasks[0].pet_name == "Mochi"


def test_loading_a_file_with_a_bad_value_raises(owner, tmp_path):
    owner.get_pet("Mochi").add_task(Task("Walk", "07:30", 30))
    path = tmp_path / "data.json"
    owner.save_to_json(path)
    path.write_text(path.read_text().replace('"07:30"', '"25:00"'))

    with pytest.raises(ValueError):
        Owner.load_from_json(path)
