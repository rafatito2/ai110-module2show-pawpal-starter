# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Output of `python main.py` (Phase 2, before the scheduler had any sorting):

```
🐾 PawPal+ demo for Rafael — Saturday Oct 31
Pets: Mochi (dog), Luna (cat)

Today's schedule (as entered)
-----------------------------
  ⬜ 18:30  Mochi    Evening walk            30 min  🟡 medium daily
  ⬜ 07:30  Mochi    Morning walk            30 min  🔴 high   daily
  ⬜ 08:00  Mochi    Breakfast               10 min  🔴 high   daily
  ⬜ 08:00  Luna     Thyroid pill             5 min  🔴 high   daily
  ⬜ 19:00  Luna     Brush coat              15 min  🟢 low    weekly
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

Sample test output:

```
.........................                                                [100%]
25 passed in 0.01s
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

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
