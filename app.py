"""PawPal+ Streamlit UI — connects to pawpal_system.py backend logic."""

import streamlit as st
from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling — add pets, create tasks, and generate a daily plan.")

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# ---------------------------------------------------------------------------
# Section 1 — Owner & first pet setup
# ---------------------------------------------------------------------------

st.header("1. Owner & Pet Setup")

with st.form("setup_form"):
    owner_name = st.text_input("Owner name", value="Jordan")
    pet_name = st.text_input("First pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    setup_submitted = st.form_submit_button("Create Owner & Pet")

if setup_submitted:
    pet = Pet(name=pet_name, species=species)
    owner = Owner(name=owner_name)
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.scheduler = Scheduler(owner)
    st.success(f"Owner '{owner_name}' created with pet '{pet_name}' ({species}).")

if st.session_state.owner is None:
    st.info("Fill in the form above to get started.")
    st.stop()

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

# Show current roster
pet_names = [p.name for p in owner.pets]
st.caption(f"Owner: **{owner.name}** | Pets: {', '.join(pet_names)}")

# --- Add additional pets ---
with st.expander("Add another pet"):
    with st.form("add_pet_form"):
        new_pet_name = st.text_input("New pet name")
        new_species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"], key="add_species")
        add_pet_submitted = st.form_submit_button("Add Pet")

    if add_pet_submitted:
        if not new_pet_name.strip():
            st.warning("Please enter a pet name.")
        elif owner.get_pet(new_pet_name):
            st.warning(f"A pet named '{new_pet_name}' already exists.")
        else:
            owner.add_pet(Pet(name=new_pet_name, species=new_species))
            st.success(f"Added '{new_pet_name}' ({new_species})!")
            st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Section 2 — Add a task
# ---------------------------------------------------------------------------

st.header("2. Add a Task")

pet_names = [p.name for p in owner.pets]

with st.form("task_form"):
    col1, col2 = st.columns(2)
    with col1:
        selected_pet = st.selectbox("Pet", pet_names)
        task_desc = st.text_input("Description", value="Morning walk")
        task_time = st.text_input("Time (HH:MM, 24-hour)", value="07:30")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=480, value=20)
        frequency = st.selectbox("Frequency", ["one-time", "daily", "weekly"])
        task_due = st.date_input("Due date", value=date.today())

    task_submitted = st.form_submit_button("Add Task")

if task_submitted:
    # Basic time format validation
    parts = task_time.split(":")
    valid_time = (
        len(parts) == 2
        and parts[0].isdigit()
        and parts[1].isdigit()
        and 0 <= int(parts[0]) <= 23
        and 0 <= int(parts[1]) <= 59
    )
    if not valid_time:
        st.error("Time must be in HH:MM 24-hour format (e.g. 07:30, 14:00).")
    elif not task_desc.strip():
        st.error("Task description cannot be empty.")
    else:
        pet = owner.get_pet(selected_pet)
        if pet:
            new_task = Task(
                description=task_desc.strip(),
                time=task_time,
                duration=int(duration),
                pet_name=selected_pet,
                frequency=frequency,
                due_date=task_due,
            )
            pet.add_task(new_task)
            st.success(f"Added '{task_desc}' for {selected_pet} at {task_time}.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Today's schedule
# ---------------------------------------------------------------------------

st.header("3. Today's Schedule")

conflicts = scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        st.warning(f"⚠️ {warning}")

plan = scheduler.generate_daily_plan()

if not plan:
    st.info("No tasks due today. Add some tasks above!")
else:
    for task in plan:
        cols = st.columns([1, 2, 3, 2, 2])
        cols[0].markdown(f"**{task.time}**")
        cols[1].write(task.pet_name)
        cols[2].write(task.description)
        cols[3].write(f"{task.duration} min · {task.frequency}")
        if cols[4].button("✓ Done", key=f"done_{task.task_id}"):
            next_task = scheduler.mark_task_complete(task.task_id)
            if next_task:
                st.success(
                    f"Done! Next '{task.description}' scheduled for {next_task.due_date}."
                )
            else:
                st.success(f"'{task.description}' marked complete.")
            st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Section 4 — All tasks with filtering
# ---------------------------------------------------------------------------

st.header("4. All Tasks")

filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    filter_pet = st.selectbox("Filter by pet", ["All"] + [p.name for p in owner.pets], key="filter_pet")
with filter_col2:
    filter_status = st.selectbox("Filter by status", ["All", "Incomplete", "Completed"], key="filter_status")

completed_filter = None
if filter_status == "Incomplete":
    completed_filter = False
elif filter_status == "Completed":
    completed_filter = True

filtered = scheduler.filter_tasks(
    pet_name=None if filter_pet == "All" else filter_pet,
    completed=completed_filter,
)
sorted_filtered = scheduler.sort_by_time(filtered)

if not sorted_filtered:
    st.info("No tasks match the current filters.")
else:
    table_data = [
        {
            "Time": t.time,
            "Pet": t.pet_name,
            "Description": t.description,
            "Duration (min)": t.duration,
            "Frequency": t.frequency,
            "Status": "Done" if t.completed else "Pending",
            "Due Date": str(t.due_date),
        }
        for t in sorted_filtered
    ]
    st.table(table_data)
