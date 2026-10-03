import os
from dataclasses import replace
from datetime import datetime, time
from pathlib import Path

import streamlit as st

from display import priority_badge, status_badge, task_label
from main import build_demo_owner
from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# Pets and tasks are saved here after every change and loaded back on startup.
# PAWPAL_DATA_FILE lets tests point the app at a throwaway file instead.
DATA_FILE = Path(os.environ.get("PAWPAL_DATA_FILE", Path(__file__).with_name("data.json")))


def use_owner(new_owner: Owner) -> None:
    """Swap in a different owner and sync the sidebar inputs to match it."""
    st.session_state.owner = new_owner
    st.session_state.owner_name = new_owner.name
    st.session_state.owner_minutes = new_owner.available_minutes


def load_saved_owner() -> Owner:
    """Load the owner from DATA_FILE, or start fresh if there's no file or it can't be read."""
    if DATA_FILE.exists():
        try:
            return Owner.load_from_json(DATA_FILE)
        except (ValueError, KeyError, TypeError) as err:
            st.session_state.load_error = f"Couldn't read {DATA_FILE.name}, so PawPal+ started fresh. ({err})"
    return Owner(name="Jordan", available_minutes=120)


# --- App memory -------------------------------------------------------------
# Streamlit reruns this whole file on every click. Anything created here would be
# rebuilt from scratch each time, so the Owner (and everything inside it) is kept
# in session_state and only loaded on the very first run.
if "owner" not in st.session_state:
    use_owner(load_saved_owner())


def mark_done(choices: list[Task], scheduler: Scheduler) -> None:
    """Button callback: finish the picked task and leave a message for the next run."""
    task = choices[st.session_state.done_choice]
    next_task = scheduler.complete_task(task)
    message = f"{task.description} for {task.pet_name} is done."
    if next_task:
        message += f" Since it repeats {task.frequency}, the next one is set for {next_task.due_date:%A, %B %d}."
    st.session_state.flash = ("success", message)


def swap_task(old: Task, new: Task) -> None:
    """Replace a task with an edited copy on the same pet."""
    pet = st.session_state.owner.get_pet(old.pet_name)
    pet.remove_task(old)
    pet.add_task(new)


def save_edit(task: Task) -> None:
    """Form callback: swap the task for an edited copy, so Task's input checks run again."""
    form = st.session_state
    key = id(task)
    description = form[f"edit_desc_{key}"].strip()
    if not description:
        form.flash = ("error", "A task needs a description, so nothing was changed.")
        return
    edited = replace(
        task,
        description=description,
        time=form[f"edit_time_{key}"].strftime("%H:%M"),
        duration_minutes=int(form[f"edit_minutes_{key}"]),
        priority=form[f"edit_priority_{key}"],
        frequency=form[f"edit_repeats_{key}"],
    )
    swap_task(task, edited)
    form.flash = ("success", f"Saved your changes to {edited.description} for {edited.pet_name}.")


def move_task(task: Task, new_time: str) -> None:
    """Button callback: move a clashing task to the suggested free time."""
    swap_task(task, replace(task, time=new_time))
    st.session_state.flash = ("success", f"Moved {task.description} for {task.pet_name} to {new_time}.")


def remove_task(task: Task) -> None:
    """Form callback: delete the task from its pet."""
    st.session_state.owner.get_pet(task.pet_name).remove_task(task)
    st.session_state.flash = ("success", f"Removed {task.description} for {task.pet_name}.")


def show_flash() -> None:
    """Show the message a callback left behind, if there is one."""
    if "flash" in st.session_state:
        # A plain if/else on purpose: Streamlit prints any bare expression to the page,
        # so a one-line "a if x else b" here would also dump the return value.
        kind, message = st.session_state.pop("flash")
        if kind == "error":
            st.error(message)
        else:
            st.success(message)


def pick_label(t: Task) -> str:
    """Short one-line name for a task, used in the pick lists."""
    return f"{t.due_date:%a %b %d}, {t.time} - {t.description} ({t.pet_name})"


def task_rows(tasks: list[Task]) -> list[dict]:
    """Turn tasks into table rows for st.dataframe."""
    return [
        {
            "Due": f"{t.due_date:%a %b %d}",
            "Time": f"{t.time}-{t.end_time()}",
            "Task": task_label(t),
            "Pet": t.pet_name,
            "Priority": priority_badge(t.priority),
            "Repeats": t.frequency,
            "Status": status_badge(t),
        }
        for t in tasks
    ]


owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

# --- Sidebar: owner settings ------------------------------------------------
with st.sidebar:
    st.header("Your settings")
    owner.name = st.text_input("Your name", key="owner_name")
    owner.available_minutes = int(
        st.number_input("Minutes for pet care today", min_value=5, max_value=720, step=5, key="owner_minutes")
    )
    st.caption("PawPal+ only plans as many tasks as fit in this time, most important first.")
    st.divider()
    st.button("Load sample data", on_click=use_owner, args=(build_demo_owner(),))
    st.button("Start over", on_click=use_owner, args=(Owner("Jordan", 120),))
    st.caption(f"Your pets and tasks are saved to `{DATA_FILE.name}` automatically.")

st.title("🐾 PawPal+")
st.caption(f"Hi {owner.name}! Add your pets and their care tasks, and PawPal+ will plan your day.")
if "load_error" in st.session_state:
    st.warning(st.session_state.pop("load_error"))

# --- Pets -------------------------------------------------------------------
# Forms come before the lists they change. Because the script runs top to bottom,
# a new pet is already saved by the time the list below gets drawn.
st.subheader("Pets")
with st.form("add_pet", clear_on_submit=True):
    col1, col2, col3 = st.columns([2, 1, 1])
    pet_name = col1.text_input("Pet name", placeholder="Mochi")
    species = col2.selectbox("Species", ["dog", "cat", "other"])
    age = col3.number_input("Age", min_value=0, max_value=40, value=1)

    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Give your pet a name first.")
        else:
            try:
                owner.add_pet(Pet(pet_name.strip(), species, int(age)))
                st.success(f"Added {pet_name.strip()}.")
            except ValueError as err:
                st.error(str(err))

if owner.pets:
    species_emoji = {"dog": "🐶", "cat": "🐱"}
    st.dataframe(
        [
            {
                "Name": f"{species_emoji.get(p.species, '🐾')} {p.name}",
                "Species": p.species,
                "Age": p.age,
                "Tasks to do": len(p.get_pending_tasks()),
            }
            for p in owner.pets
        ],
        hide_index=True,
    )
else:
    st.info("No pets yet. Add one above, or click **Load sample data** in the sidebar.")

st.divider()

# --- Tasks ------------------------------------------------------------------
st.subheader("Tasks")
if not owner.pets:
    st.info("Add a pet first, then you can give it tasks.")
else:
    with st.form("add_task", clear_on_submit=True):
        pet_choice = st.selectbox("Pet", [p.name for p in owner.pets])
        col1, col2 = st.columns([2, 1])
        description = col1.text_input("Task", placeholder="Morning walk")
        start = col2.time_input("Start time", value=time(8, 0), step=300)
        col1, col2, col3 = st.columns(3)
        duration = col1.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        priority = col2.selectbox("Priority", ["low", "medium", "high"], index=2)
        frequency = col3.selectbox("Repeats", ["once", "daily", "weekly"])

        if st.form_submit_button("Add task"):
            if not description.strip():
                st.error("Describe the task first, like \"Morning walk\".")
            else:
                task = Task(
                    description=description.strip(),
                    time=start.strftime("%H:%M"),
                    duration_minutes=int(duration),
                    priority=priority,
                    frequency=frequency,
                )
                owner.get_pet(pet_choice).add_task(task)
                st.success(f"Added \"{task.description}\" for {pet_choice} at {task.time}.")

    show_flash()

    to_do = scheduler.sort_by_time(scheduler.filter_tasks(completed=False))
    if to_do:
        col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
        col1.selectbox(
            "Mark a task done",
            options=range(len(to_do)),
            format_func=lambda i: pick_label(to_do[i]),
            key="done_choice",
        )
        col2.button("Mark done", on_click=mark_done, args=(to_do, scheduler))

    every_task = scheduler.sort_by_time(owner.get_all_tasks())
    if every_task:
        with st.expander("Edit or remove a task"):
            picked = every_task[
                st.selectbox(
                    "Task to change",
                    options=range(len(every_task)),
                    format_func=lambda i: pick_label(every_task[i]),
                    key="edit_choice",
                )
            ]
            # Keys include the task's id, so picking a different task refills the form.
            key = id(picked)
            with st.form(f"edit_task_{key}"):
                col1, col2 = st.columns([2, 1])
                col1.text_input("Task", value=picked.description, key=f"edit_desc_{key}")
                col2.time_input(
                    "Start time",
                    value=datetime.strptime(picked.time, "%H:%M").time(),
                    step=300,
                    key=f"edit_time_{key}",
                )
                col1, col2, col3 = st.columns(3)
                col1.number_input(
                    "Duration (minutes)",
                    min_value=1,
                    max_value=max(240, picked.duration_minutes),
                    value=picked.duration_minutes,
                    key=f"edit_minutes_{key}",
                )
                priorities, repeats = ["low", "medium", "high"], ["once", "daily", "weekly"]
                col2.selectbox(
                    "Priority", priorities, index=priorities.index(picked.priority), key=f"edit_priority_{key}"
                )
                col3.selectbox(
                    "Repeats", repeats, index=repeats.index(picked.frequency), key=f"edit_repeats_{key}"
                )
                col1, col2 = st.columns(2)
                col1.form_submit_button("Save changes", on_click=save_edit, args=(picked,))
                col2.form_submit_button("Remove task", on_click=remove_task, args=(picked,))

    st.markdown("**All tasks**")
    col1, col2 = st.columns(2)
    pet_filter = col1.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
    status_filter = col2.radio("Show", ["All", "To do", "Done"], horizontal=True)

    filtered = scheduler.filter_tasks(
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"All": None, "To do": False, "Done": True}[status_filter],
    )
    if filtered:
        st.dataframe(task_rows(scheduler.sort_by_time(filtered)), hide_index=True)
    elif owner.get_all_tasks():
        st.info("No tasks match these filters.")
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# --- Today's schedule -------------------------------------------------------
st.subheader("Today's schedule")
plan = scheduler.build_daily_plan()
explanation = scheduler.explain_plan(plan).replace("\n", "  \n")  # markdown line breaks

if not plan and not scheduler.skipped:
    st.info("Nothing is due today. Tasks you add for today will show up here.")
else:
    used = sum(t.duration_minutes for t in plan)
    col1, col2, col3 = st.columns(3)
    col1.metric("Tasks planned", len(plan))
    col2.metric("Minutes used", f"{used} of {owner.available_minutes}")
    col3.metric("Didn't fit", len(scheduler.skipped))

    # Each clash gets a warning plus a one-click fix: the lower-priority task (or the
    # later one, on a tie) moves to the next free time that day.
    pairs = scheduler.find_conflicting_pairs(plan)
    for (a, b), warning in zip(pairs, scheduler.detect_conflicts(plan)):
        suggestion = scheduler.suggest_move(a, b)
        if suggestion:
            to_move, new_time = suggestion
            st.warning(
                f"**Time clash:** {warning} The next free time for {to_move.description} is {new_time}.",
                icon="⚠️",
            )
            st.button(
                f"Move {to_move.description} ({to_move.pet_name}) to {new_time}",
                key=f"move_{id(to_move)}_{id(a)}_{id(b)}",
                on_click=move_task,
                args=(to_move, new_time),
            )
        else:
            st.warning(f"**Time clash:** {warning} There's no free time left today to move either one.", icon="⚠️")

    if plan:
        order = st.radio("Order plan by", ["Time", "Priority"], horizontal=True)
        shown = plan if order == "Time" else scheduler.sort_by_priority(plan)
        st.dataframe(
            [
                {
                    "Time": f"{t.time}-{t.end_time()}",
                    "Task": task_label(t),
                    "Pet": t.pet_name,
                    "Priority": priority_badge(t.priority),
                }
                for t in shown
            ],
            hide_index=True,
        )

    if scheduler.skipped:
        st.info(explanation)
    else:
        st.success(explanation)

# Save after every run, so any change made on this click is on disk before the page finishes.
owner.save_to_json(DATA_FILE)
