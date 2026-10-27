"""PawPal+ logic layer.

Classes:
- Task: one care activity (walk, feeding, meds...) with a time, duration, priority and frequency.
- Pet: a pet and the list of tasks that belong to it.
- Owner: a person with one or more pets.
- Scheduler: reads every task across the owner's pets and sorts, filters, checks conflicts,
  and handles recurring tasks.
"""

from dataclasses import dataclass, field
from datetime import date


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

    def mark_complete(self):
        pass

    def next_occurrence(self):
        pass


@dataclass
class Pet:
    name: str
    species: str = "dog"
    age: int = 0
    tasks: list = field(default_factory=list)

    def add_task(self, task):
        pass

    def list_tasks(self):
        pass

    def pending_tasks(self):
        pass

    def complete_task(self, task):
        pass


@dataclass
class Owner:
    name: str
    pets: list = field(default_factory=list)

    def add_pet(self, pet):
        pass

    def get_pet(self, name):
        pass

    def all_tasks(self):
        pass


class Scheduler:
    def __init__(self, owner):
        self.owner = owner

    def get_all_tasks(self):
        pass

    def sort_by_time(self, tasks=None):
        pass

    def filter_by_pet(self, pet_name):
        pass

    def filter_by_status(self, completed):
        pass

    def detect_conflicts(self):
        pass

    def mark_task_complete(self, task):
        pass
