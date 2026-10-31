# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

Before drawing anything I wrote down the three things a pet owner actually needs to do in the app:

1. **Add a pet** to their profile (name, species, age) so tasks have somebody to belong to.
2. **Schedule a care task** for a pet: what it is, what time, how long it takes, how important it is, and whether it repeats (once / daily / weekly).
3. **See today's schedule** across all pets in time order, with warnings when two tasks collide, and mark tasks done so repeating ones roll forward to the next day or week.

**a. Initial design**

Four classes, same as the project asked for, and I tried hard to keep it at four:

- `Task` is a dataclass with description, time as an `"HH:MM"` string, duration in minutes, priority, frequency, due date, a completed flag, and the name of the pet it belongs to. It knows how to mark itself complete and how to produce its own next occurrence.
- `Pet` is a dataclass with name, species, age and a list of tasks. It adds, lists and completes tasks. It's the only place that appends to its own task list, so `pet_name` always gets stamped.
- `Owner` is a dataclass with a name and a list of pets, plus `all_tasks()` which flattens every pet's list.
- `Scheduler` is a plain class that takes an Owner and does everything that spans pets: sort, filter, today's view, conflict check, and completing a task through the right pet.

The split I cared about most is that `Scheduler` reads but never owns data. All the lists live in Pet and Owner, so if I throw the Scheduler away nothing is lost.

**b. Design changes**

Two changes from the Phase 1 diagram:

- Originally `Scheduler.mark_task_complete()` was going to do the recurrence itself (mark done, build the copy, append it). When I asked Claude to review the skeleton it pointed out that the Scheduler would then need to know which pet's list to append to, which meant looking it up by name every time. I moved that logic into `Pet.complete_task()` and the Scheduler just finds the pet and delegates. One place owns recurrence now, and the tests for it don't even need a Scheduler.
- I added `start_minutes()` / `end_minutes()` on Task halfway through Phase 4. I had a lambda converting `"HH:MM"` to minutes inside `sort_by_time`, then needed the same thing again for conflicts, then again for the free-slot search. Three copies of the same split-and-multiply was the signal to move it onto the Task.

Phase 6 also grew the diagram with `to_dict`/`from_dict` on all three data classes and `next_available_slot` / `build_daily_plan` on the Scheduler, which came from the stretch features rather than a design change.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler looks at four things: the clock time, the duration, the priority (high/medium/low) and the day. Time and duration together give a time block, and that block is what conflict detection and the free-slot finder work with. Priority only matters when there isn't room for everything: `sort_by_priority()` for display and `build_daily_plan()` when the owner says "I have 45 minutes today", where high-priority tasks get claimed first.

I decided time was the most important constraint because that's what the README scenario is about: a busy owner who needs to know what to do *now*. Priority came second because it is the thing that breaks ties when the day is overbooked. I left out owner preferences (like "no walks before 7") because nothing in the spec defined what those would be and I didn't want to invent a config format.

**b. Tradeoffs**

Conflict detection only looks at one calendar day at a time and treats every task as starting exactly at its listed time and running exactly `duration_minutes`. A 30 minute walk at 18:30 and a vet visit at 18:45 get flagged, which is what I want, but a task at 23:50 that runs 20 minutes never gets compared with 00:05 the next day, and the scheduler has no idea that "feed Luna" and "feed Mochi" at the same time are actually fine because they take ten seconds each. I also flag conflicts for different pets, not just the same pet, since one person is doing all of it.

I think that's reasonable for this scenario. The owner is a single human, so two overlapping blocks really are a problem no matter which pet they belong to. Midnight-crossing tasks are rare for pet care, and making the check smarter (travel time, tasks that can run in parallel) would mean adding attributes the spec never asked for. The warning is advisory anyway, nothing gets blocked, so a false positive costs the user one glance.

The daily plan has a second tradeoff: it's greedy. It walks tasks in priority order and takes each one that still fits. In the demo that means a 10 minute high-priority breakfast gets picked before a 45 minute high-priority vet visit purely because 08:00 comes before 18:45, and then the vet visit no longer fits in a 45 minute budget. A real optimizer would notice the vet visit alone is a better use of the budget. I kept greedy because the output is explainable in one sentence per task, and explaining the plan was a stated requirement; an optimal knapsack answer is harder to justify to a pet owner.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude Code in VS Code for the whole project, in separate chat sessions per phase: one for design, one for core implementation, one for the algorithms, one for tests, one for docs. Keeping them separate genuinely helped, mostly because the algorithm chat never saw the Streamlit code and so never tried to "help" by touching the UI, and the test chat started from the final `pawpal_system.py` instead of a half-remembered earlier version.

The prompts that worked best were the ones that named a file and a constraint. "Based on my skeletons in pawpal_system.py, how should the Scheduler retrieve all tasks from the Owner's pets?" got a direct answer (`[t for pet in owner.pets for t in pet.tasks]` plus the suggestion to put it on Owner so the Scheduler doesn't reach two levels deep). "Make the scheduler smarter" style prompts produced lists of features I then had to cut down.

Specific things AI was good at: the `sorted()` key for `"HH:MM"` strings, explaining `dataclasses.replace` for cloning a Task, the `st.session_state` pattern, and drafting the pytest parametrize for invalid times.

**b. Judgment and verification**

The one I pushed back on hardest: when I asked for conflict detection, the first draft compared `task.time == other.time`, exactly the "same time" wording from the instructions. I asked it to walk through my demo data and it agreed that an 18:30 walk and an 18:45 vet visit would pass as fine. I had it rewrite the check as an interval overlap (`start < other.end and other.start < end`) and then wrote `test_back_to_back_tasks_are_not_a_conflict` myself first, because I was worried the rewrite would flag 08:00–08:30 followed by 08:30 as a clash. It didn't, but I only knew that because the test said so.

A smaller one: for the UML it initially suggested a `Schedule` class separate from `Scheduler` to hold a day's plan, plus a `Reminder` class. I rejected both; the day's plan is just a list of Tasks, and five classes was already more than the brief asked for.

How I verified in general: run `python main.py` after every change and read the whole output, not just the new section, and keep pytest green. The README sample output is real terminal output from the final code, not edited.

---

## 4. Testing and Verification

**a. What you tested**

32 tests across six groups: Task validation and completion, Pet/Owner containers, sorting (time, date-before-time, priority, non-mutation), filtering (pet, status, today's view), recurrence (daily, weekly, once), conflicts (same time, overlapping durations, back-to-back, completed ignored, empty owner), and the three stretch features (free-slot search, budgeted plan, JSON round trip).

The ones that mattered most were the "boundary" ones: back-to-back tasks must not be a conflict, a 20 minute task must fit in a 30 minute gap but a 45 minute task must not, and completing a one-off task must not create anything. Those are the places where an off-by-one or a `<=` vs `<` silently gives wrong answers without crashing, so a human reading the demo output might never notice.

**b. Confidence**

4 out of 5. Everything the demo and the UI call is covered, and the tests use fixed dates so they won't start failing next week. What I'd test next: tasks that cross midnight, a weekly task completed twice in one day (does it create two copies?), what happens to `data.json` when a task's date format is corrupted by hand, and the Streamlit interactions themselves, which I only checked by clicking through.

---

## 5. Reflection

**a. What went well**

The CLI-first order. By the time I opened `app.py` the logic had been run dozens of times from `main.py`, so wiring the UI was almost entirely "call the method, show the list". Every Streamlit bug I hit was a Streamlit bug (state resetting on rerun), never a logic bug.

I'm also happy with `build_daily_plan()` returning a `reasons` dict. It made the "explain the plan" requirement trivial for both the CLI and the UI, and it made the tests readable because I could assert on the reason string.

**b. What you would improve**

The `reasons` dict is keyed on `"Pet: description"`, which breaks if a pet has two tasks with the same description. I'd give Task an id. I'd also make `next_available_slot` return something richer than a string so the UI could offer "schedule it here" in one click. And the Streamlit app rebuilds the task table on every rerun; for a real app with hundreds of tasks I'd cache the sorted view.

**c. Key takeaway**

The useful part of being "lead architect" wasn't writing more code than the AI, it was deciding what *not* to build. Every time I gave a vague prompt the answer came back bigger: more classes, more attributes, more features. The design stayed clean because I kept a four-class ceiling, said no to Schedule/Reminder/Notification, and made the AI justify each method against the spec. Separate chats per phase and a reference point (the UML) to compare against were what made the no's easy to defend.
