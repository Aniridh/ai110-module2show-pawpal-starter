"""CLI demo script for PawPal+ — verifies backend logic in the terminal."""

from datetime import date
from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    # --- Setup ---
    owner = Owner(name="Jordan")

    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Add tasks intentionally out of time order to exercise sorting
    mochi.add_task(Task(description="Evening walk", time="18:00", duration=30, pet_name="Mochi", frequency="daily"))
    mochi.add_task(Task(description="Morning walk", time="07:30", duration=20, pet_name="Mochi", frequency="daily"))
    mochi.add_task(Task(description="Heartworm medication", time="08:00", duration=5, pet_name="Mochi", frequency="weekly"))
    luna.add_task(Task(description="Breakfast feeding", time="07:00", duration=10, pet_name="Luna", frequency="daily"))
    luna.add_task(Task(description="Evening playtime", time="19:00", duration=15, pet_name="Luna", frequency="daily"))

    # Add a deliberate scheduling conflict to test detection
    mochi.add_task(Task(description="Grooming session", time="07:30", duration=45, pet_name="Mochi", frequency="one-time"))

    scheduler = Scheduler(owner)

    # --- Today's Schedule ---
    print("=" * 55)
    print("          PawPal+ — Today's Schedule")
    print("=" * 55)
    plan = scheduler.generate_daily_plan()
    if plan:
        for task in plan:
            status = "[x]" if task.completed else "[ ]"
            print(
                f"  {status} {task.time}  {task.pet_name:<8}  "
                f"{task.description} ({task.duration} min, {task.frequency})"
            )
    else:
        print("  No tasks scheduled for today.")

    # --- Conflict Detection ---
    print()
    print("--- Conflict Detection ---")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            print(f"  WARNING: {warning}")
    else:
        print("  No conflicts detected.")

    # --- Recurring Task Demo ---
    print()
    print("--- Completing 'Morning walk' (daily — should auto-recur) ---")
    morning_walk = next(
        (t for t in mochi.tasks if t.description == "Morning walk"), None
    )
    if morning_walk:
        scheduler.mark_task_complete(morning_walk.task_id)
        print(f"  Marked '{morning_walk.description}' as complete.")
        next_occurrence = next(
            (t for t in mochi.tasks if t.description == "Morning walk" and not t.completed),
            None,
        )
        if next_occurrence:
            print(f"  Next occurrence created for {next_occurrence.due_date}.")

    # --- Filtering ---
    print()
    print("--- Filtering: Luna's incomplete tasks ---")
    luna_tasks = scheduler.filter_tasks(pet_name="Luna", completed=False)
    for task in luna_tasks:
        print(f"  {task.time}  {task.description}")

    print()
    print("--- Sorted full schedule (after completing morning walk) ---")
    for task in scheduler.sort_by_time():
        status = "[x]" if task.completed else "[ ]"
        print(f"  {status} {task.time}  {task.pet_name:<8}  {task.description}")

    print()
    print("=" * 55)


if __name__ == "__main__":
    main()
