from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Add your pets and their care tasks, then let PawPal+ plan your day.")

# Streamlit reruns this whole file on every click. Anything created here would be
# rebuilt from scratch each time, so the Owner (and everything inside it) is kept
# in session_state and only created on the very first run.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=120)

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

# --- Owner ------------------------------------------------------------------
st.subheader("Owner")
col1, col2 = st.columns(2)
owner.name = col1.text_input("Your name", value="Jordan")
owner.available_minutes = int(
    col2.number_input("Minutes for pet care today", min_value=5, max_value=720, value=120, step=5)
)

st.divider()

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
    st.dataframe(
        [
            {"Name": p.name, "Species": p.species, "Age": p.age, "Tasks": len(p.tasks)}
            for p in owner.pets
        ],
        hide_index=True,
    )
else:
    st.info("No pets yet. Add one above.")

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

    all_tasks = scheduler.sort_by_time(owner.get_all_tasks())
    if all_tasks:
        st.dataframe(
            [
                {
                    "Time": t.time,
                    "Task": t.description,
                    "Pet": t.pet_name,
                    "Minutes": t.duration_minutes,
                    "Priority": t.priority,
                    "Repeats": t.frequency,
                    "Done": t.completed,
                }
                for t in all_tasks
            ],
            hide_index=True,
        )
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# --- Schedule ---------------------------------------------------------------
st.subheader("Today's schedule")
if st.button("Generate schedule", type="primary"):
    plan = scheduler.build_daily_plan()
    if plan:
        st.dataframe(
            [
                {
                    "Time": f"{t.time}-{t.end_time()}",
                    "Task": t.description,
                    "Pet": t.pet_name,
                    "Priority": t.priority,
                }
                for t in plan
            ],
            hide_index=True,
        )
    # Markdown needs two spaces before a newline to show a line break.
    st.info(scheduler.explain_plan(plan).replace("\n", "  \n"))
