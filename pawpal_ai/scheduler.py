from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from .models import Owner, Task


class Scheduler:
    """Provides sorting, filtering, conflict checks, and recurrence management."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def get_all_tasks(self, include_completed: bool = True) -> List[Task]:
        tasks: List[Task] = []
        for pet in self.owner.pets:
            for task in pet.tasks:
                if include_completed or not task.completed:
                    tasks.append(task)
        return tasks

    def sort_by_time(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        selected = tasks if tasks is not None else self.get_all_tasks(include_completed=True)

        def task_key(task: Task) -> tuple[date, datetime]:
            parsed_time = datetime.strptime(task.time, "%H:%M")
            return task.due_date, parsed_time

        return sorted(selected, key=task_key)

    def sort_by_priority_then_time(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        selected = tasks if tasks is not None else self.get_all_tasks(include_completed=True)
        priority_weight = {"high": 0, "medium": 1, "low": 2}

        def task_key(task: Task) -> tuple[int, date, datetime]:
            parsed_time = datetime.strptime(task.time, "%H:%M")
            return priority_weight.get(task.priority.lower(), 1), task.due_date, parsed_time

        return sorted(selected, key=task_key)

    def filter_tasks(
        self,
        tasks: Optional[List[Task]] = None,
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> List[Task]:
        selected = tasks if tasks is not None else self.get_all_tasks(include_completed=True)
        filtered: List[Task] = []
        for task in selected:
            if completed is not None and task.completed != completed:
                continue
            if pet_name and (task.pet_name or "").lower() != pet_name.lower():
                continue
            filtered.append(task)
        return filtered

    def generate_daily_schedule(
        self,
        target_date: Optional[date] = None,
        strategy: str = "time",
    ) -> List[Task]:
        day = target_date or date.today()
        day_tasks = [
            task for task in self.get_all_tasks(include_completed=False) if task.due_date == day
        ]
        if strategy == "priority":
            return self.sort_by_priority_then_time(day_tasks)
        return self.sort_by_time(day_tasks)

    def build_priority_plan(self, target_date: Optional[date] = None) -> List[Task]:
        remaining = self.owner.available_minutes_per_day
        candidate_tasks = self.generate_daily_schedule(target_date=target_date, strategy="priority")
        chosen: List[Task] = []
        for task in candidate_tasks:
            if task.duration_minutes <= remaining:
                chosen.append(task)
                remaining -= task.duration_minutes
        return chosen

    def suggest_next_available_slot(
        self,
        duration_minutes: int,
        target_date: Optional[date] = None,
        start_time: str = "06:00",
        end_time: str = "22:00",
        increment_minutes: int = 15,
    ) -> Optional[str]:
        day = target_date or date.today()
        scheduled = self.generate_daily_schedule(target_date=day, strategy="time")
        occupied = {
            datetime.strptime(task.time, "%H:%M"): task.duration_minutes for task in scheduled
        }

        cursor = datetime.strptime(start_time, "%H:%M")
        window_end = datetime.strptime(end_time, "%H:%M")

        while cursor + timedelta(minutes=duration_minutes) <= window_end:
            candidate_end = cursor + timedelta(minutes=duration_minutes)
            overlaps = False
            for existing_start, existing_duration in occupied.items():
                existing_end = existing_start + timedelta(minutes=existing_duration)
                if cursor < existing_end and existing_start < candidate_end:
                    overlaps = True
                    break
            if not overlaps:
                return cursor.strftime("%H:%M")
            cursor += timedelta(minutes=increment_minutes)

        return None

    def mark_task_complete(self, task: Task) -> Optional[Task]:
        task.mark_complete()
        recurring = task.next_occurrence()
        if recurring:
            pet = self.owner.get_pet(task.pet_name or "")
            if pet:
                pet.add_task(recurring)
        return recurring

    def detect_conflicts(self, tasks: Optional[List[Task]] = None) -> List[str]:
        selected = tasks if tasks is not None else self.generate_daily_schedule()
        by_slot: Dict[str, List[Task]] = {}
        for task in selected:
            by_slot.setdefault(task.time, []).append(task)

        warnings: List[str] = []
        for time_slot, slot_tasks in by_slot.items():
            if len(slot_tasks) > 1:
                pet_list = ", ".join(sorted({task.pet_name or "Unknown" for task in slot_tasks}))
                warnings.append(
                    f"Conflict at {time_slot}: {len(slot_tasks)} tasks scheduled ({pet_list})."
                )
        return warnings

    def explain_schedule(self, tasks: List[Task]) -> List[str]:
        explanations: List[str] = []
        for task in tasks:
            explanations.append(
                f"{task.time} - {task.pet_name}: {task.description} "
                f"({task.duration_minutes} min, {task.priority} priority)"
            )
        return explanations
