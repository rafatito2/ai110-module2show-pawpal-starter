# AI Interactions Log

Stretch-feature documentation for PawPal+. Tool used throughout: Claude Code (Claude Fable 5.1) inside VS Code.

---

## Agent Workflow (SF7)

**What task did you give the agent?**

After the required features were committed, I opened a fresh chat and gave it `pawpal_system.py`, `main.py` and `tests/test_pawpal.py` with this task:

> Add a third algorithmic capability to the Scheduler: `next_available_slot(duration_minutes, day)` that returns the earliest "HH:MM" where a task of that length fits with no overlap against any pending task for any pet, searching 08:00–21:00 in 15 minute steps and returning None when the day is full. Then add `build_daily_plan(available_minutes, day)` that picks pending tasks greedily by priority then time, skips anything that overflows the budget or overlaps an already chosen task, and returns the plan in time order with a one-line reason per task. Reuse `start_minutes()`/`end_minutes()`; don't add new classes or attributes. Extend main.py to demo both and add tests.

**What did the agent do?**

1. Edited `pawpal_system.py`: added a `# --- planning ---` block to `Scheduler` with both methods, reusing `todays_schedule()` for the busy list and `sort_by_priority()` for plan ordering.
2. Edited `main.py`: added a "Next free slot for a 20 min grooming session" section and a "Daily plan with only 45 minutes available" section that prints the plan table, minutes used, and the reasons list.
3. Edited `tests/test_pawpal.py`: added six tests (three per feature) including the empty-day and full-day edge cases.
4. Ran `python main.py` and `python -m pytest -q` and reported 32 passing.

**What did you have to verify or fix manually?**

- The first version of `next_available_slot` built the probe times with a lambda that split the string again. I asked it to use `Task("probe", start).start_minutes()` instead so the `HH:MM` parsing has exactly one home. Small, but it is the rule I set in Phase 4.
- I checked the greedy plan by hand against the demo data. With a 45 minute budget it keeps Breakfast (10, high) and Evening walk (30, medium) and skips the 45 minute Vet appointment (high) because only 35 minutes remain after Breakfast. That is what greedy-by-priority-then-time should do, but it is not the "best" answer, so I documented it as a tradeoff in `reflection.md` §2b rather than letting the README imply the plan is optimal.
- I added the `test_daily_plan_is_returned_in_time_order_even_though_chosen_by_priority` test myself after noticing the agent's tests only checked *which* tasks were chosen, not the order the UI would display them in.

JSON persistence (`to_dict`/`from_dict`/`save_to_json`/`load_from_json` on Owner, Pet and Task) was done in the same session as a second task. The only manual fix there was asking for `date` to be stored as ISO strings rather than letting `json.dump` crash on a `date` object, which the first draft would have done.

---

## Prompt Comparison (SF11)

Same model (Claude Fable 5.1 in Claude Code), two prompting strategies for the same task: the recurrence logic for daily/weekly tasks.

| | Option A: vague, no files attached | Option B: constrained, files attached |
|-|----------|----------|
| **Model / tool used** | Claude Fable 5.1, new chat, nothing attached | Claude Fable 5.1, new chat, `pawpal_system.py` + `diagrams/uml_draft.mmd` attached |
| **Prompt** | "Add recurring task support to my pet scheduler so daily and weekly tasks repeat." | "When a Task with frequency daily/weekly is completed, create exactly one new Task for due_date + 1 day / + 1 week, same pet, same time, not completed. `once` creates nothing. Put the copy logic on Task, the append on Pet, and have Scheduler delegate. No new classes or attributes." |
| **Response summary** | Proposed a `RecurrenceRule` class with `interval`, `count`, `until`, a `Schedule` class that materialises the next 30 days of occurrences on demand, and a `generate_occurrences()` method; suggested storing `rrule` strings compatible with iCalendar. | Added `Task.next_occurrence()` using `dataclasses.replace(self, due_date=..., completed=False)`, `Pet.complete_task()` that calls it and appends, and a three-line `Scheduler.mark_task_complete()` that finds the pet and delegates. Suggested two tests. |
| **What was useful** | It made me think about "what if the owner never completes the task, should tomorrow's still appear?", which I had not considered. | Dropped straight into my design, used `replace` which I didn't know about, and matched the UML exactly. Took one review pass. |
| **Problems noticed** | Two new classes and a dependency on a calendar standard for a project whose spec says "daily or weekly". Would have doubled the UML. Also silently assumed tasks repeat whether or not they are completed, which conflicts with the project instructions ("when a task is marked complete, a new instance is created"). | `replace()` copies `pet_name` too, which is fine here but would be wrong if a task could move between pets. It did not mention that, I noticed it while reading. |
| **Decision** | Rejected in full, kept the question about never-completed tasks as a "would test next" note. | Adopted, with the recurrence tests rewritten to use a fixed date instead of `date.today()` so they stay stable. |

**Which approach did you use in your final implementation and why?**

Option B, as written, is what's in `pawpal_system.py`. The comparison made the point of the whole project obvious: the same model gave a seven-day-project answer and a ten-minute answer depending only on whether I told it the boundaries. The vague prompt was not wrong in some abstract sense, iCalendar rules are how real calendar apps do it, it was wrong for *this* spec. Attaching the UML and saying "no new classes" turned the AI from a feature generator into a pair programmer.
