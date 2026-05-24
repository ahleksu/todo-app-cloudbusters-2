"""Unit tests for TodoService reminder_at field handling."""

import pytest

from exceptions import ValidationError
from models import TodoCreate, TodoUpdate
from services.todo_service import TodoService
from store import JSONStore


@pytest.fixture
def todo_service(tmp_path):
    return TodoService(JSONStore(str(tmp_path / "todos.json")))


def test_create_with_valid_reminder_at(todo_service):
    todo = todo_service.create(
        "user-1", TodoCreate(title="Test", reminder_at="2026-05-24T09:00:00Z")
    )
    assert todo.reminder_at is not None


def test_create_without_reminder_at(todo_service):
    todo = todo_service.create("user-1", TodoCreate(title="Test"))
    assert todo.reminder_at is None


def test_create_with_invalid_reminder_at_raises(todo_service):
    with pytest.raises(ValidationError):
        todo_service.create(
            "user-1", TodoCreate(title="Test", reminder_at="not-a-datetime")
        )


def test_update_sets_reminder_at(todo_service):
    todo = todo_service.create("user-1", TodoCreate(title="Test"))
    updated = todo_service.update(
        "user-1", todo.id, TodoUpdate(reminder_at="2026-06-01T10:00:00Z")
    )
    assert updated.reminder_at is not None


def test_update_clears_reminder_at_with_null(todo_service):
    todo = todo_service.create(
        "user-1", TodoCreate(title="Test", reminder_at="2026-05-24T09:00:00Z")
    )
    updated = todo_service.update(
        "user-1", todo.id, TodoUpdate.model_validate({"reminder_at": None})
    )
    assert updated.reminder_at is None
