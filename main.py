"""CLI demo for PawPal+. Run: python main.py"""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task

PRIORITY_ICON = {"high": "🔴", "medium": "🟡", "low": "🟢"}


def print_schedule(title, tasks):
    """Print tasks as a small aligned table with a status icon per row."""
    print(f"\n{title}")
    print("-" * len(title))
    if not tasks:
        print("  (nothing scheduled)")
        return
    for t in tasks:
        status = "✅" if t.completed else "⬜"
        icon = PRIORITY_ICON[t.priority]
        print(f"  {status} {t.due_date:%a %m/%d} {t.time}  {t.pet_name:<8} {t.description:<22} "
              f"{t.duration_minutes:>3} min  {icon} {t.priority:<6} {t.frequency}")


def main():
    today = date.today()
    owner = Owner("Rafael")
    mochi = owner.add_pet(Pet("Mochi", "dog", 3))
    luna = owner.add_pet(Pet("Luna", "cat", 5))

    # Added out of order on purpose so sorting has something to do.
    mochi.add_task(Task("Evening walk", "18:30", 30, "medium", "daily", today))
    mochi.add_task(Task("Morning walk", "07:30", 30, "high", "daily", today))
    luna.add_task(Task("Thyroid pill", "08:00", 5, "high", "daily", today))
    luna.add_task(Task("Brush coat", "19:00", 15, "low", "weekly", today))
    mochi.add_task(Task("Breakfast", "08:00", 10, "high", "daily", today))
    # Deliberate clash: Luna's vet visit overlaps Mochi's evening walk.
    luna.add_task(Task("Vet appointment", "18:45", 45, "high", "once", today))

    scheduler = Scheduler(owner)
    print(f"🐾 PawPal+ demo for {owner.name} — {today:%A %b %d}")
    print(f"Pets: {', '.join(f'{p.name} ({p.species}, {p.age})' for p in owner.pets)}")

    print_schedule("Today's schedule, sorted by time", scheduler.sort_by_time(scheduler.todays_schedule()))
    print_schedule("Same tasks, sorted by priority", scheduler.sort_by_priority(scheduler.todays_schedule()))
    print_schedule("Filter: only Luna", scheduler.filter_by_pet("Luna"))
    print_schedule("Filter: only high priority", scheduler.filter_by_priority("high"))

    print("\nConflict check")
    print("--------------")
    conflicts = scheduler.detect_conflicts()
    for warning in conflicts or ["  ✅ no overlapping tasks today"]:
        print(f"  {warning}")

    print("\nMark 'Morning walk' (daily) and 'Brush coat' (weekly) complete")
    print("--------------------------------------------------------------")
    morning = next(t for t in mochi.tasks if t.description == "Morning walk")
    brush = next(t for t in luna.tasks if t.description == "Brush coat")
    for task in (morning, brush):
        follow_up = scheduler.mark_task_complete(task)
        print(f"  ✅ {task.pet_name}: {task.description} done -> next on {follow_up.due_date:%a %b %d}")

    print_schedule("Still pending today", scheduler.sort_by_time(scheduler.todays_schedule()))
    print_schedule("Completed", scheduler.filter_by_status(True))
    upcoming = [t for t in scheduler.sort_by_time() if t.due_date > today]
    print_schedule("Upcoming (auto-created by recurrence)", upcoming)


if __name__ == "__main__":
    main()
