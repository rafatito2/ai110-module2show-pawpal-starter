# PawPal+ (Module 2 Project)

**PawPal+** is a small pet-care planner: an owner adds pets, schedules care tasks for them (walks, feeding, meds, grooming), and a `Scheduler` turns that pile of tasks into a sorted, filtered, conflict-checked daily view. The logic lives in plain Python (`pawpal_system.py`), is exercised by a CLI demo (`main.py`) and a pytest suite, and is wired to a Streamlit UI (`app.py`).

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

## ✨ Features

| Feature | Where | What it does |
|---|---|---|
| Owner → Pets → Tasks model | `Owner`, `Pet`, `Task` dataclasses | Tasks carry description, `HH:MM` time, duration, priority (high/medium/low), frequency (once/daily/weekly), due date and completion flag. Bad times/priorities raise `ValueError` up front. |
| Sorting by time | `Scheduler.sort_by_time()` | Chronological across **all** pets, by date then clock time. |
| Priority scheduling | `Scheduler.sort_by_priority()` | High → medium → low, time inside each level. |
| Filtering | `filter_by_pet()`, `filter_by_status()`, `filter_by_priority()`, `todays_schedule()` | Chainable: each accepts an optional task list. |
| Conflict warnings | `Scheduler.detect_conflicts()` | Flags **overlapping time blocks** (not just identical start times) across pets. Returns warning strings, never raises. |
| Daily / weekly recurrence | `Task.next_occurrence()`, `Pet.complete_task()` | Completing a daily task creates tomorrow's copy; weekly adds 7 days; one-off creates nothing. |
| Next available slot ★ | `Scheduler.next_available_slot()` | Earliest free `HH:MM` for an N-minute task, 15-minute steps, 08:00–21:00. |
| Time-budgeted daily plan ★ | `Scheduler.build_daily_plan()` | "I have 45 minutes": greedy by priority, skips overflow and overlaps, returns a **reason per task**. |
| JSON persistence ★ | `Owner.save_to_json()` / `load_from_json()` | Whole owner/pet/task tree round-trips through `data.json`; the Streamlit app loads it on start. |
| Emoji / aligned CLI output ★ | `main.py: print_schedule()` | ⬜/✅ status, 🔴🟡🟢 priority, fixed-width columns. No extra libraries. |

★ = stretch feature.

## 🏗️ Classes

```
Owner ──owns──▶ Pet ──has──▶ Task
  ▲
  │ reads
Scheduler  (sort / filter / conflicts / plan / complete-with-recurrence)
```

- **Task**: one care activity. Knows its own time block (`start_minutes()` / `end_minutes()`) and how to clone itself for the next occurrence.
- **Pet**: identifying info + its task list. The only class that appends tasks, so every task knows its `pet_name`.
- **Owner**: name + pets, `all_tasks()` across pets, save/load.
- **Scheduler**: holds no data of its own. Everything it does spans every pet the owner has.

Full diagram: [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd) (draft from Phase 1 kept as `uml_draft.mmd`).

## 🚀 Getting started

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python main.py                   # CLI demo
python -m pytest                 # tests
streamlit run app.py             # UI
```

## 🖥️ Sample Output

Real output of `python main.py` on the final code (one owner, two pets, six tasks, one deliberate overlap):

```
🐾 PawPal+ demo for Rafael — Saturday Oct 31
Pets: Mochi (dog, 3), Luna (cat, 5)

Today's schedule, sorted by time
--------------------------------
  ⬜ Sat 10/31 07:30  Mochi    Morning walk            30 min  🔴 high   daily
  ⬜ Sat 10/31 08:00  Mochi    Breakfast               10 min  🔴 high   daily
  ⬜ Sat 10/31 08:00  Luna     Thyroid pill             5 min  🔴 high   daily
  ⬜ Sat 10/31 18:30  Mochi    Evening walk            30 min  🟡 medium daily
  ⬜ Sat 10/31 18:45  Luna     Vet appointment         45 min  🔴 high   once
  ⬜ Sat 10/31 19:00  Luna     Brush coat              15 min  🟢 low    weekly

Same tasks, sorted by priority
------------------------------
  ⬜ Sat 10/31 07:30  Mochi    Morning walk            30 min  🔴 high   daily
  ⬜ Sat 10/31 08:00  Mochi    Breakfast               10 min  🔴 high   daily
  ⬜ Sat 10/31 08:00  Luna     Thyroid pill             5 min  🔴 high   daily
  ⬜ Sat 10/31 18:45  Luna     Vet appointment         45 min  🔴 high   once
  ⬜ Sat 10/31 18:30  Mochi    Evening walk            30 min  🟡 medium daily
  ⬜ Sat 10/31 19:00  Luna     Brush coat              15 min  🟢 low    weekly

Filter: only Luna
-----------------
  ⬜ Sat 10/31 08:00  Luna     Thyroid pill             5 min  🔴 high   daily
  ⬜ Sat 10/31 19:00  Luna     Brush coat              15 min  🟢 low    weekly
  ⬜ Sat 10/31 18:45  Luna     Vet appointment         45 min  🔴 high   once

Filter: only high priority
--------------------------
  ⬜ Sat 10/31 07:30  Mochi    Morning walk            30 min  🔴 high   daily
  ⬜ Sat 10/31 08:00  Mochi    Breakfast               10 min  🔴 high   daily
  ⬜ Sat 10/31 08:00  Luna     Thyroid pill             5 min  🔴 high   daily
  ⬜ Sat 10/31 18:45  Luna     Vet appointment         45 min  🔴 high   once

Conflict check
--------------
  ⚠️ 08:00: Mochi's and Luna's 'Breakfast' (10 min) overlaps 'Thyroid pill' at 08:00
  ⚠️ 18:30: Mochi's and Luna's 'Evening walk' (30 min) overlaps 'Vet appointment' at 18:45
  ⚠️ 18:45: Luna's 'Vet appointment' (45 min) overlaps 'Brush coat' at 19:00

Mark 'Morning walk' (daily) and 'Brush coat' (weekly) complete
--------------------------------------------------------------
  ✅ Mochi: Morning walk done -> next on Sun Nov 01
  ✅ Luna: Brush coat done -> next on Sat Nov 07

Still pending today
-------------------
  ⬜ Sat 10/31 08:00  Mochi    Breakfast               10 min  🔴 high   daily
  ⬜ Sat 10/31 08:00  Luna     Thyroid pill             5 min  🔴 high   daily
  ⬜ Sat 10/31 18:30  Mochi    Evening walk            30 min  🟡 medium daily
  ⬜ Sat 10/31 18:45  Luna     Vet appointment         45 min  🔴 high   once
```

### Stretch output: free slot, budgeted plan, persistence

Same run, continued. The plan is **greedy by priority then time**, which is why the 45-minute vet visit loses out once the 10-minute breakfast has claimed part of the budget (documented as a tradeoff in `reflection.md`):

```
Next free slot for a 20 min grooming session
---------------------------------------------
  📅 earliest start: 08:15

Daily plan with only 45 minutes available
--------------------------------------------
  ✅ 08:00  Mochi    Breakfast               10 min  🔴 high
  ✅ 18:30  Mochi    Evening walk            30 min  🟡 medium
  ⏱️  40 of 45 min used
  Why:
    • Mochi: Breakfast -> kept: high priority, 10 min, fits at 08:00
    • Luna: Thyroid pill -> skipped: overlaps 'Breakfast' at 08:00
    • Luna: Vet appointment -> skipped: needs 45 min but only 35 min left
    • Mochi: Evening walk -> kept: medium priority, 30 min, fits at 18:30

Persistence: saved to data.json and reloaded Rafael with 2 pets / 8 tasks

Completed
---------
  ✅ Sat 10/31 07:30  Mochi    Morning walk            30 min  🔴 high   daily
  ✅ Sat 10/31 19:00  Luna     Brush coat              15 min  🟢 low    weekly

Upcoming (auto-created by recurrence)
-------------------------------------
  ⬜ Sun 11/01 07:30  Mochi    Morning walk            30 min  🔴 high   daily
  ⬜ Sat 11/07 19:00  Luna     Brush coat              15 min  🟢 low    weekly
```

## 🧪 Testing PawPal+

```bash
python -m pytest          # run the suite
python -m pytest -v       # one line per test
```

`tests/test_pawpal.py` covers, in order:

- **Task**: `mark_complete()` flips status; `HH:MM` gets normalised; bad times, priorities and frequencies raise `ValueError` instead of silently breaking sorting later.
- **Pet / Owner**: adding a task increases the pet's count and stamps `pet_name`; an owner's `all_tasks()` spans every pet; `get_pet()` is case-insensitive and returns `None` when missing.
- **Sorting**: chronological order across pets, date ordered before clock time, priority order high → low, and sorting never mutates the pets' lists.
- **Filtering**: by pet, by completion status, and `todays_schedule()` ignoring other days and finished tasks.
- **Recurrence**: completing a daily task creates tomorrow's copy on the same pet, weekly adds 7 days, one-off creates nothing.
- **Conflicts**: identical times across pets, overlapping durations with different start times, back-to-back tasks are *not* a conflict, completed tasks are ignored, and an owner with no pets returns empty results everywhere.
- **Stretch**: free-slot search (skips busy blocks, uses gaps, returns `None` on a full day), budgeted plan (priority wins, overflow and overlap skipped with reasons, time-ordered result), and a JSON save/load round trip using pytest's `tmp_path`.

Sample test output:

```
................................                                         [100%]
32 passed in 0.02s
```

**Confidence level: ★★★★☆ (4/5).** Every behaviour the demo relies on has a test, including the edge cases that bit me while writing it (back-to-back vs overlapping). The missing star is for things I know are untested: tasks that cross midnight, and the Streamlit layer itself, which I only checked by hand in the browser.

## 📐 Smarter Scheduling

All of these live on `Scheduler` in `pawpal_system.py` and work across every pet the owner has, not one pet at a time.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_by_priority()` | `sorted()` with a tuple key: `(due_date, minutes-since-midnight)`. Priority sort uses `PRIORITY_ORDER` (high → medium → low) and falls back to time inside each level. Both return a new list and never mutate the pets' task lists. |
| Filtering | `Scheduler.filter_by_pet()`, `filter_by_status()`, `filter_by_priority()`, `todays_schedule()` | Each takes an optional `tasks` list so filters can be chained (e.g. filter by pet, then sort). Pet names compare case-insensitively. |
| Conflict handling | `Scheduler.detect_conflicts(day)` | Checks pending tasks on one day for **overlapping time blocks** (start < other end), not just identical start times. Returns a list of warning strings; an empty list means the day is clean. It never raises, so the UI can show `st.warning` per item. Tasks are sorted first so the inner loop can `break` early. |
| Recurring tasks | `Task.next_occurrence()`, `Pet.complete_task()`, `Scheduler.mark_task_complete()` | Marking a `daily` task complete creates a copy due `today + 1 day`; `weekly` adds 7 days; `once` creates nothing. Uses `dataclasses.replace` + `timedelta` so the copy keeps time, duration, priority and pet. The Scheduler routes completion through the task's `Pet` so recurrence logic lives in exactly one place. |

### Stretch: planning, persistence, formatting

| Feature | Method(s) / files | Notes |
|---|---|---|
| Next available slot | `Scheduler.next_available_slot(duration, day, start, end, step)` | Builds a busy list from `todays_schedule()`, walks candidate starts in 15-min steps, returns the first with no overlap, or `None`. |
| Priority-based daily plan | `Scheduler.build_daily_plan(available_minutes, day)` | Greedy over `sort_by_priority()`. Returns `{plan, skipped, minutes_used, minutes_available, reasons}`. The CLI and the UI both print `reasons` so the plan explains itself. |
| Persistence | `Task/Pet/Owner.to_dict()`, `from_dict()`, `Owner.save_to_json()`, `Owner.load_from_json()` in `pawpal_system.py`; `app.py` sidebar buttons; `main.py` demo | Dates are stored as ISO strings. `app.py` loads `data.json` automatically if it exists, and has Save / Load buttons. `data.json` is git-ignored so each run starts from the user's own data. Files modified: `pawpal_system.py`, `app.py`, `main.py`, `.gitignore`. |
| Output formatting | `main.py: print_schedule()`, `PRIORITY_ICON`; `app.py: task_rows()` | Emoji status (⬜ / ✅) and priority (🔴 🟡 🟢), fixed-width columns via f-string alignment, `st.table` / `st.warning` / `st.success` in the UI. Standard library only. |

## 📸 Demo Walkthrough

`streamlit run app.py` opens a single page:

1. **Sidebar: owner + save/load.** Type the owner's name. "Save to data.json" writes everything to disk; "Load" reads it back; the app also auto-loads `data.json` on first start so pets survive a restart.
2. **Pets.** Add a pet with name, species and age. Duplicate names are refused. A table shows each pet with its pending-task count.
3. **Schedule a task.** Pick a pet, enter a task, time (`HH:MM`), minutes, priority, repeat rule and date. Invalid times (`25:00`) show an error from the `Task` validator. If the new task overlaps anything already scheduled that day, a `st.warning` with the exact clash appears right under the form.
4. **Next free slot.** A slider ("Slot length to look for") drives `next_available_slot()`; the caption updates live with the earliest start that fits today.
5. **Today's schedule.** Conflict warnings for today sit at the top (or a green "No overlapping tasks"). Filter by pet and status, sort by time or priority, then pick a pending task and press **Done**. Daily/weekly tasks report when their next copy was created and appear under **Upcoming**.
6. **Build today's plan.** Choose how many minutes you have, press **Generate plan**, and get the chosen tasks in time order, minutes used, and a "Why these tasks?" list with one reason per task (kept / skipped for budget / skipped for overlap).

**Example workflow:** add Mochi (dog) and Luna (cat) → schedule Morning walk 07:30 daily high, Breakfast 08:00 daily high for Mochi, Thyroid pill 08:00 daily high for Luna → the Breakfast/Thyroid overlap is flagged immediately → press Done on Morning walk → tomorrow's copy shows in Upcoming → set the budget to 45 min and generate the plan.

**Key Scheduler behaviours visible in the UI:** time/priority sorting (dropdown), pet/status filtering (dropdowns), overlap warnings (yellow boxes), recurrence (Done button + Upcoming), budgeted plan with reasons (expander).

**CLI equivalent:** the full `python main.py` transcript is in the Sample Output section above.

*Screenshots are optional per the brief; the walkthrough and CLI output above are the gradable demo.*
