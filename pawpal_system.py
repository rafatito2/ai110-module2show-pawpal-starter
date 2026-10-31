"""PawPal+ logic layer.

Classes:
- Task: one care activity (walk, feeding, meds...) with a time, duration, priority and frequency.
- Pet: a pet and the list of tasks that belong to it.
- Owner: a person with one or more pets.
- Scheduler: reads every task across the owner's pets and sorts, filters, checks conflicts,
  and handles recurring tasks.
"""

import json
from dataclasses import asdict, dataclass, field, replace
from datetime import date, timedelta

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
FREQUENCIES = ("once", "daily", "weekly")


@dataclass
class Task:
    description: str
    time: str                      # "HH:MM", 24h
    duration_minutes: int = 15
    priority: str = "medium"       # low | medium | high
    frequency: str = "once"        # once | daily | weekly
    due_date: date = field(default_factory=date.today)
    completed: bool = False
    pet_name: str = ""             # filled in by Pet.add_task

    def __post_init__(self):
        """Normalise text fields and reject values the rest of the system can't handle."""
        self.priority = self.priority.lower()
        self.frequency = self.frequency.lower()
        if self.priority not in PRIORITY_ORDER:
            raise ValueError(f"priority must be one of {list(PRIORITY_ORDER)}, got {self.priority!r}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {FREQUENCIES}, got {self.frequency!r}")
        hours, minutes = self.time.split(":")
        if not (0 <= int(hours) < 24 and 0 <= int(minutes) < 60):
            raise ValueError(f"time must be HH:MM in 24h format, got {self.time!r}")
        self.time = f"{int(hours):02d}:{int(minutes):02d}"

    def mark_complete(self):
        """Flag this task as done."""
        self.completed = True

    def start_minutes(self):
        """Minutes after midnight when the task starts; handy for sorting and overlap checks."""
        hours, minutes = self.time.split(":")
        return int(hours) * 60 + int(minutes)

    def end_minutes(self):
        """Minutes after midnight when the task ends."""
        return self.start_minutes() + self.duration_minutes

    def next_occurrence(self):
        """Return a fresh copy of this task for the next day/week, or None for one-off tasks."""
        if self.frequency == "daily":
            return replace(self, due_date=self.due_date + timedelta(days=1), completed=False)
        if self.frequency == "weekly":
            return replace(self, due_date=self.due_date + timedelta(weeks=1), completed=False)
        return None

    def to_dict(self):
        """Plain-dict version of the task so it can be written to JSON."""
        data = asdict(self)
        data["due_date"] = self.due_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data):
        """Rebuild a Task from the dict produced by to_dict()."""
        data = dict(data)
        data["due_date"] = date.fromisoformat(data["due_date"])
        return cls(**data)


@dataclass
class Pet:
    name: str
    species: str = "dog"
    age: int = 0
    tasks: list = field(default_factory=list)

    def add_task(self, task):
        """Attach a task to this pet and return it."""
        task.pet_name = self.name
        self.tasks.append(task)
        return task

    def list_tasks(self):
        """All tasks for this pet, in the order they were added."""
        return list(self.tasks)

    def pending_tasks(self):
        """Tasks that have not been marked complete yet."""
        return [t for t in self.tasks if not t.completed]

    def remove_task(self, task):
        """Delete a task from this pet."""
        self.tasks.remove(task)

    def complete_task(self, task):
        """Mark a task done; if it repeats, schedule the next one and return it."""
        task.mark_complete()
        follow_up = task.next_occurrence()
        if follow_up is not None:
            self.add_task(follow_up)
        return follow_up

    def to_dict(self):
        """Plain-dict version of the pet and its tasks."""
        return {"name": self.name, "species": self.species, "age": self.age,
                "tasks": [t.to_dict() for t in self.tasks]}

    @classmethod
    def from_dict(cls, data):
        """Rebuild a Pet (and its tasks) from the dict produced by to_dict()."""
        pet = cls(data["name"], data.get("species", "dog"), data.get("age", 0))
        for task_data in data.get("tasks", []):
            pet.add_task(Task.from_dict(task_data))
        return pet


@dataclass
class Owner:
    name: str
    pets: list = field(default_factory=list)

    def add_pet(self, pet):
        """Register a pet with this owner and return it."""
        self.pets.append(pet)
        return pet

    def get_pet(self, name):
        """Find a pet by name (case-insensitive) or return None."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def all_tasks(self):
        """Every task across every pet."""
        return [task for pet in self.pets for task in pet.tasks]

    # --- persistence ------------------------------------------------------------

    def to_dict(self):
        """Plain-dict version of the owner, pets and tasks."""
        return {"name": self.name, "pets": [p.to_dict() for p in self.pets]}

    @classmethod
    def from_dict(cls, data):
        """Rebuild an Owner tree from the dict produced by to_dict()."""
        owner = cls(data["name"])
        for pet_data in data.get("pets", []):
            owner.add_pet(Pet.from_dict(pet_data))
        return owner

    def save_to_json(self, path="data.json"):
        """Write the whole owner/pet/task tree to a JSON file."""
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.to_dict(), handle, indent=2)
        return path

    @classmethod
    def load_from_json(cls, path="data.json"):
        """Read an owner back from a JSON file written by save_to_json()."""
        with open(path, encoding="utf-8") as handle:
            return cls.from_dict(json.load(handle))


class Scheduler:
    """The brain: works on tasks across all of an owner's pets."""

    def __init__(self, owner):
        self.owner = owner

    def get_all_tasks(self):
        """Every task for every pet the owner has."""
        return self.owner.all_tasks()

    def todays_schedule(self, day=None):
        """Pending tasks due on `day` (default today), across all pets."""
        day = day or date.today()
        return [t for t in self.get_all_tasks() if t.due_date == day and not t.completed]

    # --- sorting --------------------------------------------------------------

    def sort_by_time(self, tasks=None):
        """Return tasks ordered by date then clock time (earliest first). Leaves the input alone."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return sorted(tasks, key=lambda t: (t.due_date, t.start_minutes()))

    def sort_by_priority(self, tasks=None):
        """Return tasks ordered high -> medium -> low, and by time inside each priority."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return sorted(tasks, key=lambda t: (PRIORITY_ORDER[t.priority], t.due_date, t.start_minutes()))

    # --- filtering ------------------------------------------------------------

    def filter_by_pet(self, pet_name, tasks=None):
        """Only the tasks that belong to the named pet (case-insensitive)."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return [t for t in tasks if t.pet_name.lower() == pet_name.lower()]

    def filter_by_status(self, completed, tasks=None):
        """Only completed tasks (True) or only pending tasks (False)."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return [t for t in tasks if t.completed == completed]

    def filter_by_priority(self, priority, tasks=None):
        """Only the tasks at the given priority level."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return [t for t in tasks if t.priority == priority.lower()]

    # --- conflicts ------------------------------------------------------------

    def detect_conflicts(self, day=None):
        """Return a warning string for every pair of pending tasks on `day` whose time
        blocks overlap. Two tasks overlap when one starts before the other ends.
        Returns an empty list when the day is clean; never raises."""
        tasks = self.sort_by_time(self.todays_schedule(day))
        warnings = []
        for i, first in enumerate(tasks):
            for second in tasks[i + 1:]:
                if second.start_minutes() >= first.end_minutes():
                    break  # sorted by time, so nothing later can overlap `first`
                who = (f"{first.pet_name}'s" if first.pet_name == second.pet_name
                       else f"{first.pet_name}'s and {second.pet_name}'s")
                warnings.append(
                    f"⚠️ {first.time}: {who} '{first.description}' ({first.duration_minutes} min) "
                    f"overlaps '{second.description}' at {second.time}"
                )
        return warnings

    # --- planning ---------------------------------------------------------------

    def next_available_slot(self, duration_minutes, day=None, start="08:00", end="21:00", step=15):
        """Earliest "HH:MM" on `day` where a task of `duration_minutes` fits without overlapping
        any pending task for any pet. Candidates move in `step` minute increments between
        `start` and `end`. Returns None when the day is full."""
        busy = [(t.start_minutes(), t.end_minutes()) for t in self.todays_schedule(day)]
        window_start = Task("probe", start).start_minutes()
        window_end = Task("probe", end).start_minutes()
        candidate = window_start
        while candidate + duration_minutes <= window_end:
            candidate_end = candidate + duration_minutes
            if all(candidate_end <= b_start or candidate >= b_end for b_start, b_end in busy):
                return f"{candidate // 60:02d}:{candidate % 60:02d}"
            candidate += step
        return None

    def build_daily_plan(self, available_minutes, day=None):
        """Pick which pending tasks fit into `available_minutes` on `day`.

        Greedy by priority (high first), then by time inside the same priority. A task is
        skipped when it would push the total over budget or when its time block overlaps a
        task already in the plan. Returns a dict with the chosen tasks in time order,
        the skipped tasks, minutes used, and one reason string per task."""
        chosen, skipped, reasons, used = [], [], {}, 0
        for task in self.sort_by_priority(self.todays_schedule(day)):
            key = f"{task.pet_name}: {task.description}"
            clash = next((c for c in chosen
                          if task.start_minutes() < c.end_minutes() and c.start_minutes() < task.end_minutes()),
                         None)
            if used + task.duration_minutes > available_minutes:
                skipped.append(task)
                reasons[key] = (f"skipped: needs {task.duration_minutes} min but only "
                                f"{available_minutes - used} min left")
            elif clash is not None:
                skipped.append(task)
                reasons[key] = f"skipped: overlaps '{clash.description}' at {clash.time}"
            else:
                chosen.append(task)
                used += task.duration_minutes
                reasons[key] = f"kept: {task.priority} priority, {task.duration_minutes} min, fits at {task.time}"
        return {
            "plan": self.sort_by_time(chosen),
            "skipped": skipped,
            "minutes_used": used,
            "minutes_available": available_minutes,
            "reasons": reasons,
        }

    # --- completion + recurrence ------------------------------------------------

    def mark_task_complete(self, task):
        """Complete a task through its pet so recurrence is handled in one place."""
        pet = self.owner.get_pet(task.pet_name)
        if pet is None:
            raise ValueError(f"No pet named {task.pet_name!r} for task {task.description!r}")
        return pet.complete_task(task)
