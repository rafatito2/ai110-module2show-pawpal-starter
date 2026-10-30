"""PawPal+ logic layer.

Classes:
- Task: one care activity (walk, feeding, meds...) with a time, duration, priority and frequency.
- Pet: a pet and the list of tasks that belong to it.
- Owner: a person with one or more pets.
- Scheduler: reads every task across the owner's pets and sorts, filters, checks conflicts,
  and handles recurring tasks.
"""

from dataclasses import dataclass, field, replace
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

    # --- completion + recurrence ------------------------------------------------

    def mark_task_complete(self, task):
        """Complete a task through its pet so recurrence is handled in one place."""
        pet = self.owner.get_pet(task.pet_name)
        if pet is None:
            raise ValueError(f"No pet named {task.pet_name!r} for task {task.description!r}")
        return pet.complete_task(task)
