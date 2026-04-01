"""Automated test suite for PawPal+ scheduling system."""

import pytest
from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_owner():
    """Owner with two pets and a handful of non-conflicting tasks."""
    owner = Owner(name="Jordan")

    dog = Pet(name="Mochi", species="dog")
    dog.add_task(Task(description="Morning walk", time="07:30", duration=20, pet_name="Mochi", frequency="daily"))
    dog.add_task(Task(description="Evening walk", time="18:00", duration=30, pet_name="Mochi", frequency="daily"))
    dog.add_task(Task(description="Heartworm med", time="08:00", duration=5, pet_name="Mochi", frequency="weekly"))

    cat = Pet(name="Luna", species="cat")
    cat.add_task(Task(description="Breakfast", time="07:00", duration=10, pet_name="Luna", frequency="daily"))
    cat.add_task(Task(description="Evening play", time="19:00", duration=15, pet_name="Luna", frequency="daily"))

    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner


@pytest.fixture
def scheduler(sample_owner):
    return Scheduler(sample_owner)


# ---------------------------------------------------------------------------
# Task completion
# ---------------------------------------------------------------------------


def test_mark_complete_changes_status():
    """mark_complete() must flip completed to True."""
    task = Task(description="Feed cat", time="08:00", duration=5, pet_name="Luna")
    task.mark_complete()
    assert task.completed is True


def test_task_addition_increases_count():
    """Adding a task to a Pet must increase its task count by exactly one."""
    pet = Pet(name="Buddy", species="dog")
    before = len(pet.tasks)
    pet.add_task(Task(description="Walk", time="09:00", duration=20, pet_name="Buddy"))
    assert len(pet.tasks) == before + 1


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------


def test_sort_by_time_returns_chronological_order(scheduler):
    """sort_by_time() must return tasks in ascending HH:MM order."""
    sorted_tasks = scheduler.sort_by_time()
    times = [t.time for t in sorted_tasks]
    assert times == sorted(times)


def test_sort_handles_empty_owner():
    """sort_by_time() on an owner with no pets must return an empty list."""
    owner = Owner(name="Empty")
    s = Scheduler(owner)
    assert s.sort_by_time() == []


def test_sort_by_time_accepts_explicit_task_list(scheduler, sample_owner):
    """Passing an explicit list to sort_by_time() must sort only those tasks."""
    tasks = sample_owner.get_all_tasks()
    # Reverse them, then sort — result should be chronological.
    reversed_tasks = list(reversed(tasks))
    result = scheduler.sort_by_time(reversed_tasks)
    times = [t.time for t in result]
    assert times == sorted(times)


# ---------------------------------------------------------------------------
# Recurrence
# ---------------------------------------------------------------------------


def test_daily_task_creates_next_day_occurrence():
    """Completing a daily task must produce a new task dated one day later."""
    today = date.today()
    task = Task(
        description="Morning walk",
        time="07:30",
        duration=20,
        pet_name="Mochi",
        frequency="daily",
        due_date=today,
    )
    new_task = task.mark_complete()
    assert new_task is not None
    assert new_task.due_date == today + timedelta(days=1)
    assert new_task.completed is False


def test_weekly_task_creates_next_week_occurrence():
    """Completing a weekly task must produce a new task dated seven days later."""
    today = date.today()
    task = Task(
        description="Bath time",
        time="10:00",
        duration=30,
        pet_name="Mochi",
        frequency="weekly",
        due_date=today,
    )
    new_task = task.mark_complete()
    assert new_task is not None
    assert new_task.due_date == today + timedelta(weeks=1)


def test_one_time_task_does_not_recur():
    """Completing a one-time task must return None (no new task created)."""
    task = Task(description="Vet visit", time="14:00", duration=60, pet_name="Luna", frequency="one-time")
    new_task = task.mark_complete()
    assert new_task is None


def test_scheduler_attaches_recurring_task_to_pet(sample_owner, scheduler):
    """mark_task_complete() must add the new recurring task to the correct pet."""
    mochi = sample_owner.get_pet("Mochi")
    walk = next(t for t in mochi.tasks if t.description == "Morning walk")
    before_count = len(mochi.tasks)
    scheduler.mark_task_complete(walk.task_id)
    assert len(mochi.tasks) == before_count + 1


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------


def test_conflict_detected_for_same_pet_same_time(sample_owner, scheduler):
    """Two tasks for the same pet at the same time must produce a conflict warning."""
    mochi = sample_owner.get_pet("Mochi")
    mochi.add_task(Task(description="Medication", time="07:30", duration=5, pet_name="Mochi"))
    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) >= 1
    assert any("07:30" in c for c in conflicts)


def test_no_conflict_for_different_times(scheduler):
    """Tasks at distinct times for the same pet must not generate any warnings."""
    conflicts = scheduler.detect_conflicts()
    assert conflicts == []


def test_no_conflict_same_time_different_pets(sample_owner, scheduler):
    """The same time slot is only a conflict within the same pet, not across pets."""
    # Luna already has Breakfast at 07:00; adding Mochi task at 07:00 should be fine
    mochi = sample_owner.get_pet("Mochi")
    mochi.add_task(Task(description="Morning meds", time="07:00", duration=5, pet_name="Mochi"))
    conflicts = scheduler.detect_conflicts()
    assert conflicts == []


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def test_filter_by_pet_name(scheduler):
    """filter_tasks(pet_name=...) must return only tasks belonging to that pet."""
    luna_tasks = scheduler.filter_tasks(pet_name="Luna")
    assert all(t.pet_name == "Luna" for t in luna_tasks)
    assert len(luna_tasks) > 0


def test_filter_by_completion_status(sample_owner, scheduler):
    """filter_tasks(completed=False) must exclude all completed tasks."""
    mochi = sample_owner.get_pet("Mochi")
    mochi.tasks[0].mark_complete()
    incomplete = scheduler.filter_tasks(completed=False)
    assert all(not t.completed for t in incomplete)


def test_filter_combined(sample_owner, scheduler):
    """filter_tasks with both pet_name and completed filters must apply both constraints."""
    luna = sample_owner.get_pet("Luna")
    luna.tasks[0].mark_complete()
    result = scheduler.filter_tasks(pet_name="Luna", completed=False)
    assert all(t.pet_name == "Luna" and not t.completed for t in result)


# ---------------------------------------------------------------------------
# Daily plan generation
# ---------------------------------------------------------------------------


def test_generate_daily_plan_excludes_completed(sample_owner, scheduler):
    """generate_daily_plan() must not include tasks already marked complete."""
    mochi = sample_owner.get_pet("Mochi")
    mochi.tasks[0].mark_complete()
    plan = scheduler.generate_daily_plan()
    assert all(not t.completed for t in plan)


def test_generate_daily_plan_is_sorted(scheduler):
    """generate_daily_plan() must return tasks in ascending time order."""
    plan = scheduler.generate_daily_plan()
    times = [t.time for t in plan]
    assert times == sorted(times)


def test_generate_daily_plan_empty_for_no_pets():
    """generate_daily_plan() with no pets must return an empty list."""
    owner = Owner(name="NoPets")
    s = Scheduler(owner)
    assert s.generate_daily_plan() == []
