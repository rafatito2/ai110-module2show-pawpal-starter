"""PawPal+ Streamlit UI. Run: streamlit run app.py"""

import os
from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

DATA_FILE = "data.json"
PRIORITY_ICON = {"high": "🔴", "medium": "🟡", "low": "🟢"}

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# --- Application memory -------------------------------------------------------
# Streamlit reruns this file on every click, so the Owner lives in session_state
# and is only created (or loaded from disk) the first time the page loads.
if "owner" not in st.session_state:
    if os.path.exists(DATA_FILE):
        st.session_state.owner = Owner.load_from_json(DATA_FILE)
        st.toast(f"Loaded saved data from {DATA_FILE}")
    else:
        st.session_state.owner = Owner("Jordan")

owner = st.session_state.owner
scheduler = Scheduler(owner)

# A message queued before st.rerun() so it survives the refresh.
if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))


def task_rows(tasks):
    """Rows for st.table / st.dataframe."""
    return [
        {"Done": "✅" if t.completed else "⬜", "Date": t.due_date.strftime("%a %m/%d"), "Time": t.time,
         "Pet": t.pet_name, "Task": t.description, "Min": t.duration_minutes,
         "Priority": f"{PRIORITY_ICON[t.priority]} {t.priority}", "Repeats": t.frequency}
        for t in tasks
    ]


# --- Sidebar: owner + persistence --------------------------------------------
with st.sidebar:
    st.header("Owner")
    owner.name = st.text_input("Owner name", value=owner.name)
    st.header("Save / load")
    if st.button("💾 Save to data.json"):
        owner.save_to_json(DATA_FILE)
        st.success("Saved.")
    if st.button("📂 Load from data.json"):
        if os.path.exists(DATA_FILE):
            st.session_state.owner = Owner.load_from_json(DATA_FILE)
            st.rerun()
        else:
            st.error("No data.json yet. Save first.")
    if st.button("🗑️ Start over (memory only)"):
        st.session_state.owner = Owner(owner.name)
        st.rerun()

# --- Pets ---------------------------------------------------------------------
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
    st.table([{"Pet": p.name, "Species": p.species, "Age": p.age,
               "Pending tasks": len(p.pending_tasks())} for p in owner.pets])
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
                clashes = scheduler.detect_conflicts(due)
                for warning in clashes:
                    st.warning(warning)
            except ValueError as err:
                st.error(str(err))

    free = scheduler.next_available_slot(int(st.session_state.get("slot_len", 20)))
    st.caption(f"Next free {st.session_state.get('slot_len', 20)} min slot today: "
               f"**{free or 'none, the day is full'}**")
    st.slider("Slot length to look for (min)", 5, 120, 20, 5, key="slot_len")

# --- Today's schedule ---------------------------------------------------------
st.divider()
st.subheader("Today's schedule")

conflicts = scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        st.warning(warning)
else:
    st.success("No overlapping tasks today.")

f1, f2, f3 = st.columns(3)
pet_filter = f1.selectbox("Pet", ["All"] + [p.name for p in owner.pets])
status_filter = f2.selectbox("Status", ["Pending", "Completed", "All"])
sort_mode = f3.selectbox("Sort by", ["Time", "Priority"])

tasks = scheduler.get_all_tasks()
tasks = [t for t in tasks if t.due_date == date.today()]
if pet_filter != "All":
    tasks = scheduler.filter_by_pet(pet_filter, tasks)
if status_filter == "Pending":
    tasks = scheduler.filter_by_status(False, tasks)
elif status_filter == "Completed":
    tasks = scheduler.filter_by_status(True, tasks)
tasks = scheduler.sort_by_time(tasks) if sort_mode == "Time" else scheduler.sort_by_priority(tasks)

if tasks:
    st.table(task_rows(tasks))
    pending = [t for t in tasks if not t.completed]
    if pending:
        label = {f"{t.time} {t.pet_name}: {t.description}": t for t in pending}
        pick = st.selectbox("Mark complete", list(label))
        if st.button("✅ Done"):
            follow_up = scheduler.mark_task_complete(label[pick])
            if follow_up:
                st.session_state.flash = (f"Done. Next '{follow_up.description}' scheduled for "
                                          f"{follow_up.due_date:%a %b %d} at {follow_up.time}.")
            else:
                st.session_state.flash = "Done."
            st.rerun()
else:
    st.info("Nothing matches those filters today.")

# --- Daily plan ---------------------------------------------------------------
st.divider()
st.subheader("Build today's plan")
budget = st.slider("Minutes you have available today", 15, 480, 90, 15)
if st.button("Generate plan"):
    plan = scheduler.build_daily_plan(budget)
    if plan["plan"]:
        st.success(f"{len(plan['plan'])} task(s), {plan['minutes_used']} of {budget} min used.")
        st.table(task_rows(plan["plan"]))
    else:
        st.info("Nothing fits in that budget (or nothing is pending today).")
    if plan["skipped"]:
        st.warning(f"Skipped {len(plan['skipped'])} task(s). See reasons below.")
    with st.expander("Why these tasks?", expanded=True):
        for key, why in plan["reasons"].items():
            st.markdown(f"- **{key}** → {why}")

# --- Upcoming -----------------------------------------------------------------
upcoming = [t for t in scheduler.sort_by_time() if t.due_date > date.today() and not t.completed]
if upcoming:
    with st.expander(f"Upcoming ({len(upcoming)})"):
        st.table(task_rows(upcoming))
