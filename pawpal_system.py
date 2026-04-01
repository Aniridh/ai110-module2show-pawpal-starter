"""PawPal+ system logic — Owner, Pet, Task, and Scheduler classes."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


@dataclass
class Task:
    """Represents a single pet care activity (walk, feeding, medication, etc.)."""

    description: str
    time: str  # 24-hour "HH:MM" format
    duration: int  # minutes
    pet_name: str
    frequency: str = "one-time"  # "one-time", "daily", or "weekly"
    completed: bool = False
    due_date: date = field(default_factory=date.today)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task complete and return the next occurrence for recurring tasks."""
        self.completed = True
        if self.frequency == "daily":
            return Task(
                description=self.description,
                time=self.time,
                duration=self.duration,
                pet_name=self.pet_name,
                frequency=self.frequency,
                due_date=self.due_date + timedelta(days=1),
            )
        if self.frequency == "weekly":
            return Task(
                description=self.description,
                time=self.time,
                duration=self.duration,
                pet_name=self.pet_name,
                frequency=self.frequency,
                due_date=self.due_date + timedelta(weeks=1),
            )
        return None


@dataclass
class Pet:
    """Represents a pet and the care tasks assigned to it."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> bool:
        """Remove a task by ID. Returns True if a task was found and removed."""
        original = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.task_id != task_id]
        return len(self.tasks) < original

    def get_tasks(self) -> list[Task]:
        """Return a copy of all tasks for this pet."""
        return list(self.tasks)


@dataclass
class Owner:
    """Represents a pet owner who manages one or more pets."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's roster."""
        self.pets.append(pet)

    def get_pet(self, name: str) -> Optional[Pet]:
        """Return a pet by name (case-insensitive), or None if not found."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all pets owned."""
        tasks: list[Task] = []
        for pet in self.pets:
            tasks.extend(pet.get_tasks())
        return tasks


class Scheduler:
    """Scheduling brain: retrieves, organizes, and manages tasks across all pets."""

    def __init__(self, owner: Owner) -> None:
        """Initialize the scheduler with an Owner instance."""
        self.owner = owner

    def sort_by_time(self, tasks: Optional[list[Task]] = None) -> list[Task]:
        """Return tasks sorted in chronological order by HH:MM time string."""
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        return sorted(tasks, key=lambda t: t.time)

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> list[Task]:
        """Filter tasks by pet name and/or completion status.

        Passing None for a parameter means "no filter on that dimension".
        """
        tasks = self.owner.get_all_tasks()
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet_name.lower() == pet_name.lower()]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        return tasks

    def detect_conflicts(self) -> list[str]:
        """Return warning strings for tasks scheduled at the same time for the same pet.

        Only checks for exact time-slot collisions (not overlapping durations).
        """
        seen: dict[tuple[str, str], str] = {}
        warnings: list[str] = []
        for task in self.owner.get_all_tasks():
            key = (task.pet_name.lower(), task.time)
            if key in seen:
                warnings.append(
                    f"Conflict: '{task.description}' and '{seen[key]}' are both "
                    f"scheduled at {task.time} for {task.pet_name}."
                )
            else:
                seen[key] = task.description
        return warnings

    def mark_task_complete(self, task_id: str) -> Optional[Task]:
        """Mark a task complete by ID and attach the next occurrence to the pet if recurring."""
        for pet in self.owner.pets:
            for task in pet.tasks:
                if task.task_id == task_id:
                    new_task = task.mark_complete()
                    if new_task:
                        pet.add_task(new_task)
                    return new_task
        return None

    def generate_daily_plan(self) -> list[Task]:
        """Return today's incomplete tasks sorted chronologically by scheduled time."""
        today = date.today()
        pending = [
            t
            for t in self.owner.get_all_tasks()
            if not t.completed and t.due_date <= today
        ]
        return self.sort_by_time(pending)
