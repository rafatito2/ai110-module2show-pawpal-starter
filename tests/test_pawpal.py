from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task

TODAY = date(2026, 10, 31)


def build_owner():
    """Owner with two pets and tasks added out of order, used by most tests."""
    owner = Owner("Rafael")
    mochi = owner.add_pet(Pet("Mochi", "dog", 3))
    luna = owner.add_pet(Pet("Luna", "cat", 5))
    mochi.add_task(Task("Evening walk", "18:30", 30, "medium", "daily", TODAY))
    mochi.add_task(Task("Morning walk", "07:30", 30, "high", "daily", TODAY))
    luna.add_task(Task("Thyroid pill", "08:00", 5, "high", "daily", TODAY))
    luna.add_task(Task("Brush coat", "19:00", 15, "low", "weekly", TODAY))
    return owner


# --- Task -----------------------------------------------------------------------

def test_mark_complete_changes_status():
    task = Task("Morning walk", "07:30")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_task_time_is_normalised_to_two_digits():
    assert Task("Nap", "7:5").time == "07:05"


@pytest.mark.parametrize("bad", ["25:00", "12:60", "noon"])
def test_task_rejects_invalid_time(bad):
    with pytest.raises(ValueError):
        Task("Bad", bad)


def test_task_rejects_unknown_priority_and_frequency():
    with pytest.raises(ValueError):
        Task("Walk", "08:00", priority="urgent")
    with pytest.raises(ValueError):
        Task("Walk", "08:00", frequency="monthly")


# --- Pet / Owner ----------------------------------------------------------------

def test_adding_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog", 3)
    assert len(pet.list_tasks()) == 0
    pet.add_task(Task("Breakfast", "08:00"))
    assert len(pet.list_tasks()) == 1
    assert pet.tasks[0].pet_name == "Mochi"


def test_pet_with_no_tasks_has_empty_pending_list():
    assert Pet("Ghost").pending_tasks() == []


def test_owner_all_tasks_spans_every_pet():
    owner = build_owner()
    assert len(owner.all_tasks()) == 4
    assert {t.pet_name for t in owner.all_tasks()} == {"Mochi", "Luna"}


def test_owner_get_pet_is_case_insensitive_and_returns_none_when_missing():
    owner = build_owner()
    assert owner.get_pet("luna").name == "Luna"
    assert owner.get_pet("Rex") is None


# --- Sorting --------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order_across_pets():
    scheduler = Scheduler(build_owner())
    times = [(t.time, t.pet_name) for t in scheduler.sort_by_time()]
    assert times == [("07:30", "Mochi"), ("08:00", "Luna"), ("18:30", "Mochi"), ("19:00", "Luna")]


def test_sort_by_time_orders_by_date_before_clock_time():
    owner = Owner("O")
    pet = owner.add_pet(Pet("P"))
    pet.add_task(Task("Later date, earlier clock", "06:00", due_date=TODAY + timedelta(days=1)))
    pet.add_task(Task("Today, later clock", "22:00", due_date=TODAY))
    ordered = Scheduler(owner).sort_by_time()
    assert [t.description for t in ordered] == ["Today, later clock", "Later date, earlier clock"]


def test_sort_does_not_mutate_pet_task_lists():
    owner = build_owner()
    before = [t.description for t in owner.all_tasks()]
    Scheduler(owner).sort_by_time()
    Scheduler(owner).sort_by_priority()
    assert [t.description for t in owner.all_tasks()] == before


def test_sort_by_priority_puts_high_first_then_time():
    scheduler = Scheduler(build_owner())
    ordered = [(t.priority, t.time) for t in scheduler.sort_by_priority()]
    assert ordered == [("high", "07:30"), ("high", "08:00"), ("medium", "18:30"), ("low", "19:00")]


# --- Filtering ------------------------------------------------------------------

def test_filter_by_pet_returns_only_that_pets_tasks():
    scheduler = Scheduler(build_owner())
    luna_tasks = scheduler.filter_by_pet("luna")
    assert len(luna_tasks) == 2
    assert all(t.pet_name == "Luna" for t in luna_tasks)


def test_filter_by_status_splits_completed_and_pending():
    owner = build_owner()
    scheduler = Scheduler(owner)
    scheduler.get_all_tasks()[0].mark_complete()
    assert len(scheduler.filter_by_status(True)) == 1
    assert len(scheduler.filter_by_status(False)) == 3


def test_todays_schedule_excludes_other_days_and_completed_tasks():
    owner = build_owner()
    pet = owner.get_pet("Mochi")
    pet.add_task(Task("Tomorrow thing", "09:00", due_date=TODAY + timedelta(days=1)))
    pet.tasks[0].mark_complete()
    today = Scheduler(owner).todays_schedule(TODAY)
    assert len(today) == 3
    assert all(t.due_date == TODAY and not t.completed for t in today)


# --- Recurrence -----------------------------------------------------------------

def test_completing_daily_task_creates_task_for_next_day():
    owner = build_owner()
    scheduler = Scheduler(owner)
    walk = next(t for t in owner.all_tasks() if t.description == "Morning walk")
    follow_up = scheduler.mark_task_complete(walk)
    assert walk.completed is True
    assert follow_up is not None
    assert follow_up.due_date == TODAY + timedelta(days=1)
    assert follow_up.completed is False
    assert follow_up.time == walk.time and follow_up.pet_name == "Mochi"
    assert follow_up in owner.get_pet("Mochi").tasks


def test_completing_weekly_task_moves_one_week_ahead():
    owner = build_owner()
    brush = next(t for t in owner.all_tasks() if t.description == "Brush coat")
    follow_up = Scheduler(owner).mark_task_complete(brush)
    assert follow_up.due_date == TODAY + timedelta(weeks=1)


def test_completing_one_off_task_creates_nothing():
    owner = Owner("O")
    pet = owner.add_pet(Pet("P"))
    vet = pet.add_task(Task("Vet", "10:00", frequency="once", due_date=TODAY))
    assert Scheduler(owner).mark_task_complete(vet) is None
    assert len(pet.tasks) == 1


# --- Conflicts ------------------------------------------------------------------

def test_detect_conflicts_flags_identical_times_across_pets():
    owner = Owner("O")
    owner.add_pet(Pet("A")).add_task(Task("Feed A", "08:00", 10, due_date=TODAY))
    owner.add_pet(Pet("B")).add_task(Task("Feed B", "08:00", 10, due_date=TODAY))
    warnings = Scheduler(owner).detect_conflicts(TODAY)
    assert len(warnings) == 1
    assert "08:00" in warnings[0] and "Feed A" in warnings[0] and "Feed B" in warnings[0]


def test_detect_conflicts_flags_overlapping_durations_not_just_same_start():
    owner = Owner("O")
    pet = owner.add_pet(Pet("Mochi"))
    pet.add_task(Task("Walk", "18:30", 30, due_date=TODAY))
    pet.add_task(Task("Vet", "18:45", 45, due_date=TODAY))
    assert len(Scheduler(owner).detect_conflicts(TODAY)) == 1


def test_back_to_back_tasks_are_not_a_conflict():
    owner = Owner("O")
    pet = owner.add_pet(Pet("Mochi"))
    pet.add_task(Task("Walk", "08:00", 30, due_date=TODAY))
    pet.add_task(Task("Breakfast", "08:30", 10, due_date=TODAY))
    assert Scheduler(owner).detect_conflicts(TODAY) == []


def test_completed_tasks_do_not_cause_conflicts():
    owner = Owner("O")
    pet = owner.add_pet(Pet("Mochi"))
    done = pet.add_task(Task("Walk", "08:00", 30, due_date=TODAY))
    pet.add_task(Task("Vet", "08:00", 30, due_date=TODAY))
    done.mark_complete()
    assert Scheduler(owner).detect_conflicts(TODAY) == []


def test_empty_owner_has_no_conflicts_and_empty_schedule():
    scheduler = Scheduler(Owner("Nobody"))
    assert scheduler.detect_conflicts(TODAY) == []
    assert scheduler.todays_schedule(TODAY) == []
    assert scheduler.sort_by_time() == []


# --- Stretch: next available slot -----------------------------------------------

def test_next_available_slot_skips_busy_blocks():
    owner = Owner("O")
    pet = owner.add_pet(Pet("Mochi"))
    pet.add_task(Task("Walk", "08:00", 30, due_date=TODAY))
    pet.add_task(Task("Breakfast", "08:30", 15, due_date=TODAY))
    assert Scheduler(owner).next_available_slot(20, TODAY) == "08:45"


def test_next_available_slot_uses_gap_between_tasks_when_it_fits():
    owner = Owner("O")
    pet = owner.add_pet(Pet("Mochi"))
    pet.add_task(Task("Walk", "08:00", 30, due_date=TODAY))
    pet.add_task(Task("Pill", "09:00", 5, due_date=TODAY))
    # 08:30-09:00 is a 30 min gap, so a 20 min task fits at 08:30.
    assert Scheduler(owner).next_available_slot(20, TODAY) == "08:30"
    # A 45 min task does not fit in the gap and lands after the pill, on the next 15 min step.
    assert Scheduler(owner).next_available_slot(45, TODAY) == "09:15"


def test_next_available_slot_returns_none_when_day_is_full():
    owner = Owner("O")
    owner.add_pet(Pet("Mochi")).add_task(Task("All day", "08:00", 13 * 60, due_date=TODAY))
    assert Scheduler(owner).next_available_slot(15, TODAY) is None


# --- Stretch: daily plan with a time budget --------------------------------------

def test_daily_plan_prefers_high_priority_within_budget():
    owner = Owner("O")
    pet = owner.add_pet(Pet("Mochi"))
    pet.add_task(Task("Long low", "09:00", 60, "low", due_date=TODAY))
    pet.add_task(Task("Short high", "10:00", 10, "high", due_date=TODAY))
    pet.add_task(Task("Medium", "11:00", 20, "medium", due_date=TODAY))
    plan = Scheduler(owner).build_daily_plan(30, TODAY)
    assert [t.description for t in plan["plan"]] == ["Short high", "Medium"]
    assert [t.description for t in plan["skipped"]] == ["Long low"]
    assert plan["minutes_used"] == 30
    assert "only" in plan["reasons"]["Mochi: Long low"]


def test_daily_plan_skips_overlapping_task_and_explains_why():
    owner = Owner("O")
    owner.add_pet(Pet("A")).add_task(Task("Walk A", "08:00", 30, "high", due_date=TODAY))
    owner.add_pet(Pet("B")).add_task(Task("Walk B", "08:15", 30, "medium", due_date=TODAY))
    plan = Scheduler(owner).build_daily_plan(120, TODAY)
    assert [t.description for t in plan["plan"]] == ["Walk A"]
    assert plan["reasons"]["B: Walk B"].startswith("skipped: overlaps")


def test_daily_plan_is_returned_in_time_order_even_though_chosen_by_priority():
    owner = build_owner()
    plan = Scheduler(owner).build_daily_plan(240, TODAY)
    times = [t.time for t in plan["plan"]]
    assert times == sorted(times)
    assert plan["skipped"] == []


# --- Stretch: persistence ----------------------------------------------------------

def test_save_and_load_round_trip(tmp_path):
    owner = build_owner()
    Scheduler(owner).mark_task_complete(owner.all_tasks()[0])  # one completed + one recurrence
    path = owner.save_to_json(tmp_path / "data.json")
    loaded = Owner.load_from_json(path)
    assert loaded.name == owner.name
    assert [p.name for p in loaded.pets] == ["Mochi", "Luna"]
    assert [t.to_dict() for t in loaded.all_tasks()] == [t.to_dict() for t in owner.all_tasks()]
    assert isinstance(loaded.all_tasks()[0].due_date, date)
