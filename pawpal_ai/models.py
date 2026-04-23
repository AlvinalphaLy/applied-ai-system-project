from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Task:
    """Represents a single pet-care activity."""

    description: str
    time: str
    frequency: str = "once"
    priority: str = "medium"
    duration_minutes: int = 30
    due_date: date = field(default_factory=date.today)
    completed: bool = False
    pet_name: Optional[str] = None

    def mark_complete(self) -> None:
        self.completed = True

    def next_occurrence(self) -> Optional["Task"]:
        frequency = self.frequency.lower()
        if frequency not in {"daily", "weekly"}:
            return None

        offset_days = 1 if frequency == "daily" else 7
        return Task(
            description=self.description,
            time=self.time,
            frequency=self.frequency,
            priority=self.priority,
            duration_minutes=self.duration_minutes,
            due_date=self.due_date + timedelta(days=offset_days),
            completed=False,
            pet_name=self.pet_name,
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "description": self.description,
            "time": self.time,
            "frequency": self.frequency,
            "priority": self.priority,
            "duration_minutes": self.duration_minutes,
            "due_date": self.due_date.isoformat(),
            "completed": self.completed,
            "pet_name": self.pet_name,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "Task":
        return cls(
            description=str(payload.get("description", "")),
            time=str(payload.get("time", "00:00")),
            frequency=str(payload.get("frequency", "once")),
            priority=str(payload.get("priority", "medium")),
            duration_minutes=int(payload.get("duration_minutes", 30)),
            due_date=date.fromisoformat(str(payload.get("due_date", date.today().isoformat()))),
            completed=bool(payload.get("completed", False)),
            pet_name=str(payload.get("pet_name")) if payload.get("pet_name") else None,
        )


@dataclass
class Pet:
    name: str
    species: str
    age: Optional[int] = None
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        task.pet_name = self.name
        self.tasks.append(task)

    def task_count(self) -> int:
        return len(self.tasks)

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "Pet":
        pet = cls(
            name=str(payload.get("name", "")),
            species=str(payload.get("species", "other")),
            age=int(payload["age"]) if payload.get("age") is not None else None,
        )
        for task_payload in payload.get("tasks", []):
            pet.add_task(Task.from_dict(task_payload))
        return pet


class Owner:
    def __init__(
        self,
        name: str,
        available_minutes_per_day: int = 120,
        preferences: Optional[Dict[str, str]] = None,
    ) -> None:
        self.name = name
        self.available_minutes_per_day = available_minutes_per_day
        self.preferences = preferences or {}
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        existing_names = {p.name.lower() for p in self.pets}
        if pet.name.lower() in existing_names:
            raise ValueError(f"Pet '{pet.name}' already exists.")
        self.pets.append(pet)

    def get_pet(self, name: str) -> Optional[Pet]:
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def add_task_to_pet(self, pet_name: str, task: Task) -> None:
        pet = self.get_pet(pet_name)
        if pet is None:
            raise ValueError(f"Pet '{pet_name}' was not found.")
        pet.add_task(task)

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "available_minutes_per_day": self.available_minutes_per_day,
            "preferences": self.preferences,
            "pets": [pet.to_dict() for pet in self.pets],
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "Owner":
        owner = cls(
            name=str(payload.get("name", "Owner")),
            available_minutes_per_day=int(payload.get("available_minutes_per_day", 120)),
            preferences=dict(payload.get("preferences", {})),
        )
        for pet_payload in payload.get("pets", []):
            owner.add_pet(Pet.from_dict(pet_payload))
        return owner

    def save_to_json(self, file_path: str = "data.json") -> None:
        Path(file_path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load_from_json(cls, file_path: str = "data.json") -> "Owner":
        path = Path(file_path)
        if not path.exists():
            return cls(name="Jordan")
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(payload)
