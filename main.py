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
        print(f"  {status} {t.time}  {t.pet_name:<8} {t.description:<22} {t.duration_minutes:>3} min  "
              f"{icon} {t.priority:<6} {t.frequency}")


def main():
    today = date.today()
    owner = Owner("Rafael")
    mochi = owner.add_pet(Pet("Mochi", "dog", 3))
    luna = owner.add_pet(Pet("Luna", "cat", 5))

    # Added out of order on purpose so sorting has something to do later.
    mochi.add_task(Task("Evening walk", "18:30", 30, "medium", "daily", today))
    mochi.add_task(Task("Morning walk", "07:30", 30, "high", "daily", today))
    luna.add_task(Task("Thyroid pill", "08:00", 5, "high", "daily", today))
    luna.add_task(Task("Brush coat", "19:00", 15, "low", "weekly", today))
    mochi.add_task(Task("Breakfast", "08:00", 10, "high", "daily", today))

    scheduler = Scheduler(owner)
    print(f"🐾 PawPal+ demo for {owner.name} — {today:%A %b %d}")
    print(f"Pets: {', '.join(f'{p.name} ({p.species})' for p in owner.pets)}")
    print_schedule("Today's schedule (as entered)", scheduler.todays_schedule())


if __name__ == "__main__":
    main()
