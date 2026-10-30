"""PawPal+ Streamlit UI. Run: streamlit run app.py"""

from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# --- Application memory -------------------------------------------------------
# Streamlit reruns this file on every click, so the Owner lives in session_state
# and is only created the first time the page loads.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")

owner = st.session_state.owner
scheduler = Scheduler(owner)

# --- Owner + pets -------------------------------------------------------------
st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)

st.subheader("Pets")
with st.form("add_pet", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    pet_name = c1.text_input("Pet name", value="Mochi")
    species = c2.selectbox("Species", ["dog", "cat", "other"])
    age = c3.number_input("Age", min_value=0, max_value=40, value=2)
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Give the pet a name first.")
        elif owner.get_pet(pet_name):
            st.error(f"You already have a pet named {pet_name}.")
        else:
            owner.add_pet(Pet(pet_name.strip(), species, int(age)))
            st.success(f"Added {pet_name}.")

if owner.pets:
    st.table([{"Pet": p.name, "Species": p.species, "Age": p.age, "Tasks": len(p.tasks)} for p in owner.pets])
else:
    st.info("No pets yet. Add one above.")

# --- Tasks --------------------------------------------------------------------
st.subheader("Schedule a task")
if not owner.pets:
    st.caption("Add a pet before scheduling tasks.")
else:
    with st.form("add_task", clear_on_submit=True):
        c1, c2 = st.columns(2)
        pet_choice = c1.selectbox("Pet", [p.name for p in owner.pets])
        description = c2.text_input("Task", value="Morning walk")
        c3, c4, c5, c6 = st.columns(4)
        time_str = c3.text_input("Time (HH:MM)", value="08:00")
        duration = c4.number_input("Minutes", min_value=1, max_value=240, value=20)
        priority = c5.selectbox("Priority", ["high", "medium", "low"])
        frequency = c6.selectbox("Repeats", ["once", "daily", "weekly"])
        due = st.date_input("Date", value=date.today())
        if st.form_submit_button("Add task"):
            try:
                task = Task(description.strip(), time_str, int(duration), priority, frequency, due)
                owner.get_pet(pet_choice).add_task(task)
                st.success(f"Scheduled '{task.description}' for {pet_choice} at {task.time}.")
            except ValueError as err:
                st.error(str(err))

# --- Today's schedule ---------------------------------------------------------
st.divider()
st.subheader("Today's schedule")
todays = scheduler.todays_schedule()
if todays:
    st.table([
        {"Time": t.time, "Pet": t.pet_name, "Task": t.description,
         "Minutes": t.duration_minutes, "Priority": t.priority, "Repeats": t.frequency}
        for t in todays
    ])
else:
    st.info("Nothing scheduled for today.")
