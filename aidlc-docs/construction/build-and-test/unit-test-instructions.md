# Unit Test Instructions — Reminders & Notifications

This document covers unit tests for both **Unit 2 (Reminder Trigger Logic)** and **Unit 1 (Notification Backend)**.

## Test Framework
- **Framework**: pytest
- **Install**: `pip install pytest`

---

## Unit 2 Tests

### tests/test_reminder_checker.py

Tests for the pure `check_user()` function:

```python
"""Unit tests for reminder_checker.check_user() function."""

import pytest
from datetime import datetime, date, timezone, timedelta
from services.reminder_checker import check_user


class TestCheckUserReminderDetection:
    """Tests for reminder_at detection logic."""

    def test_detects_due_reminder(self):
        past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        todos = [{"id": "todo-1", "user_id": "user-1", "title": "Buy groceries", "status": "pending", "due_date": None, "reminder_at": past_time}]
        results = check_user("user-1", todos, [])
        assert results == [("todo-1", "reminder", "Reminder: Buy groceries")]

    def test_skips_future_reminder(self):
        future_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        todos = [{"id": "todo-1", "user_id": "user-1", "title": "Buy groceries", "status": "pending", "due_date": None, "reminder_at": future_time}]
        assert check_user("user-1", todos, []) == []

    def test_skips_done_todo_reminder(self):
        past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        todos = [{"id": "todo-1", "user_id": "user-1", "title": "Buy groceries", "status": "done", "due_date": None, "reminder_at": past_time}]
        assert check_user("user-1", todos, []) == []

    def test_skips_existing_reminder_notification(self):
        past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        todos = [{"id": "todo-1", "user_id": "user-1", "title": "Buy groceries", "status": "pending", "due_date": None, "reminder_at": past_time}]
        existing = [{"id": "n1", "user_id": "user-1", "todo_id": "todo-1", "type": "reminder", "is_read": False}]
        assert check_user("user-1", todos, existing) == []

    def test_skips_null_reminder_at(self):
        todos = [{"id": "todo-1", "user_id": "user-1", "title": "Buy groceries", "status": "pending", "due_date": None, "reminder_at": None}]
        assert check_user("user-1", todos, []) == []


class TestCheckUserOverdueDetection:
    """Tests for overdue (due_date) detection logic."""

    def test_detects_overdue_todo(self):
        past_date = (date.today() - timedelta(days=1)).isoformat()
        todos = [{"id": "todo-1", "user_id": "user-1", "title": "Submit report", "status": "pending", "due_date": past_date, "reminder_at": None}]
        results = check_user("user-1", todos, [])
        assert results == [("todo-1", "overdue", "Overdue: Submit report")]

    def test_skips_future_due_date(self):
        future_date = (date.today() + timedelta(days=1)).isoformat()
        todos = [{"id": "todo-1", "user_id": "user-1", "title": "Submit report", "status": "pending", "due_date": future_date, "reminder_at": None}]
        assert check_user("user-1", todos, []) == []

    def test_skips_today_due_date(self):
        today_str = date.today().isoformat()
        todos = [{"id": "todo-1", "user_id": "user-1", "title": "Submit report", "status": "pending", "due_date": today_str, "reminder_at": None}]
        assert check_user("user-1", todos, []) == []

    def test_skips_done_todo_overdue(self):
        past_date = (date.today() - timedelta(days=1)).isoformat()
        todos = [{"id": "todo-1", "user_id": "user-1", "title": "Submit report", "status": "done", "due_date": past_date, "reminder_at": None}]
        assert check_user("user-1", todos, []) == []

    def test_skips_existing_overdue_notification(self):
        past_date = (date.today() - timedelta(days=1)).isoformat()
        todos = [{"id": "todo-1", "user_id": "user-1", "title": "Submit report", "status": "pending", "due_date": past_date, "reminder_at": None}]
        existing = [{"id": "n1", "user_id": "user-1", "todo_id": "todo-1", "type": "overdue", "is_read": False}]
        assert check_user("user-1", todos, existing) == []


class TestCheckUserCombined:
    """Tests for combined reminder + overdue scenarios."""

    def test_detects_both_reminder_and_overdue(self):
        past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        past_date = (date.today() - timedelta(days=1)).isoformat()
        todos = [{"id": "todo-1", "user_id": "user-1", "title": "Submit report", "status": "pending", "due_date": past_date, "reminder_at": past_time}]
        results = check_user("user-1", todos, [])
        assert {r[1] for r in results} == {"reminder", "overdue"}

    def test_empty_todos_list(self):
        assert check_user("user-1", [], []) == []

    def test_handles_invalid_datetime_gracefully(self):
        todos = [{"id": "todo-1", "user_id": "user-1", "title": "Bad date", "status": "pending", "due_date": "not-a-date", "reminder_at": "not-a-datetime"}]
        assert check_user("user-1", todos, []) == []
```

### tests/test_todo_service_reminder.py

Tests for TodoService reminder_at handling:

```python
"""Unit tests for TodoService reminder_at field handling."""

import pytest
from services.todo_service import TodoService
from models import TodoCreate, TodoUpdate
from store import JSONStore
from exceptions import ValidationError


@pytest.fixture
def todo_service(tmp_path):
    return TodoService(JSONStore(str(tmp_path / "todos.json")))


def test_create_with_valid_reminder_at(todo_service):
    todo = todo_service.create("user-1", TodoCreate(title="Test", reminder_at="2026-05-24T09:00:00Z"))
    assert todo.reminder_at is not None

def test_create_without_reminder_at(todo_service):
    todo = todo_service.create("user-1", TodoCreate(title="Test"))
    assert todo.reminder_at is None

def test_create_with_invalid_reminder_at_raises(todo_service):
    with pytest.raises(ValidationError):
        todo_service.create("user-1", TodoCreate(title="Test", reminder_at="not-a-datetime"))

def test_update_sets_reminder_at(todo_service):
    todo = todo_service.create("user-1", TodoCreate(title="Test"))
    updated = todo_service.update("user-1", todo.id, TodoUpdate(reminder_at="2026-06-01T10:00:00Z"))
    assert updated.reminder_at is not None

def test_update_clears_reminder_at_with_null(todo_service):
    todo = todo_service.create("user-1", TodoCreate(title="Test", reminder_at="2026-05-24T09:00:00Z"))
    updated = todo_service.update("user-1", todo.id, TodoUpdate.model_validate({"reminder_at": None}))
    assert updated.reminder_at is None
```

---

## Unit 1 Tests

### tests/test_notification_service.py

Tests for the `NotificationService` class:

```python
"""Unit tests for NotificationService."""

import pytest
from services.notification_service import NotificationService
from store import JSONStore
from exceptions import NotFoundError


@pytest.fixture
def notif_service(tmp_path):
    return NotificationService(JSONStore(str(tmp_path / "notifications.json")))


class TestCreate:
    def test_creates_notification(self, notif_service):
        n = notif_service.create("user-1", "todo-1", "reminder", "Reminder: Buy groceries")
        assert n.user_id == "user-1"
        assert n.todo_id == "todo-1"
        assert n.type.value == "reminder"
        assert n.message == "Reminder: Buy groceries"
        assert n.is_read is False
        assert n.id  # UUID generated
        assert n.created_at is not None

    def test_creates_overdue_notification(self, notif_service):
        n = notif_service.create("user-1", "todo-1", "overdue", "Overdue: Submit report")
        assert n.type.value == "overdue"

    def test_create_does_not_dedup(self, notif_service):
        """create() does NOT dedup by itself — caller's responsibility."""
        notif_service.create("user-1", "todo-1", "reminder", "msg")
        notif_service.create("user-1", "todo-1", "reminder", "msg")
        notifications, _ = notif_service.list_for_user("user-1")
        assert len(notifications) == 2


class TestExists:
    def test_returns_true_when_match(self, notif_service):
        notif_service.create("user-1", "todo-1", "reminder", "msg")
        assert notif_service.exists("user-1", "todo-1", "reminder") is True

    def test_returns_false_when_no_match(self, notif_service):
        assert notif_service.exists("user-1", "todo-1", "reminder") is False

    def test_distinguishes_user_id(self, notif_service):
        notif_service.create("user-1", "todo-1", "reminder", "msg")
        assert notif_service.exists("user-2", "todo-1", "reminder") is False

    def test_distinguishes_todo_id(self, notif_service):
        notif_service.create("user-1", "todo-1", "reminder", "msg")
        assert notif_service.exists("user-1", "todo-2", "reminder") is False

    def test_distinguishes_type(self, notif_service):
        notif_service.create("user-1", "todo-1", "reminder", "msg")
        assert notif_service.exists("user-1", "todo-1", "overdue") is False


class TestListForUser:
    def test_returns_empty_list_for_no_notifications(self, notif_service):
        notifications, count = notif_service.list_for_user("user-1")
        assert notifications == []
        assert count == 0

    def test_returns_only_users_notifications(self, notif_service):
        notif_service.create("user-1", "todo-1", "reminder", "msg-1")
        notif_service.create("user-2", "todo-2", "reminder", "msg-2")
        notifications, _ = notif_service.list_for_user("user-1")
        assert len(notifications) == 1
        assert notifications[0].user_id == "user-1"

    def test_unread_count_reflects_full_unread_count(self, notif_service):
        # Create 25 notifications, all unread
        for i in range(25):
            notif_service.create("user-1", f"todo-{i}", "reminder", f"msg-{i}")
        notifications, unread_count = notif_service.list_for_user("user-1")
        # List is capped at 20 but unread_count is full 25
        assert len(notifications) == 20
        assert unread_count == 25

    def test_orders_desc_by_created_at(self, notif_service):
        n1 = notif_service.create("user-1", "todo-1", "reminder", "first")
        n2 = notif_service.create("user-1", "todo-2", "reminder", "second")
        n3 = notif_service.create("user-1", "todo-3", "reminder", "third")
        notifications, _ = notif_service.list_for_user("user-1")
        # Most recently created appears first
        assert notifications[0].id == n3.id
        assert notifications[-1].id == n1.id

    def test_unread_count_excludes_read(self, notif_service):
        n = notif_service.create("user-1", "todo-1", "reminder", "msg")
        notif_service.create("user-1", "todo-2", "reminder", "msg")
        notif_service.mark_as_read("user-1", n.id)
        _, unread_count = notif_service.list_for_user("user-1")
        assert unread_count == 1


class TestMarkAsRead:
    def test_marks_notification_read(self, notif_service):
        n = notif_service.create("user-1", "todo-1", "reminder", "msg")
        updated = notif_service.mark_as_read("user-1", n.id)
        assert updated.is_read is True

    def test_raises_not_found_for_missing(self, notif_service):
        with pytest.raises(NotFoundError):
            notif_service.mark_as_read("user-1", "missing-id")

    def test_raises_not_found_for_other_user(self, notif_service):
        n = notif_service.create("user-1", "todo-1", "reminder", "msg")
        with pytest.raises(NotFoundError):
            notif_service.mark_as_read("user-2", n.id)


class TestMarkAllAsRead:
    def test_marks_all_unread(self, notif_service):
        notif_service.create("user-1", "todo-1", "reminder", "msg")
        notif_service.create("user-1", "todo-2", "reminder", "msg")
        notif_service.create("user-1", "todo-3", "overdue", "msg")
        marked = notif_service.mark_all_as_read("user-1")
        assert marked == 3

    def test_returns_zero_when_all_already_read(self, notif_service):
        n = notif_service.create("user-1", "todo-1", "reminder", "msg")
        notif_service.mark_as_read("user-1", n.id)
        marked = notif_service.mark_all_as_read("user-1")
        assert marked == 0

    def test_does_not_affect_other_users(self, notif_service):
        notif_service.create("user-1", "todo-1", "reminder", "msg")
        notif_service.create("user-2", "todo-2", "reminder", "msg")
        marked = notif_service.mark_all_as_read("user-1")
        assert marked == 1
        _, u2_unread = notif_service.list_for_user("user-2")
        assert u2_unread == 1


class TestClearAll:
    def test_deletes_all_users_notifications(self, notif_service):
        notif_service.create("user-1", "todo-1", "reminder", "msg")
        notif_service.create("user-1", "todo-2", "overdue", "msg")
        notif_service.clear_all("user-1")
        notifications, count = notif_service.list_for_user("user-1")
        assert notifications == []
        assert count == 0

    def test_does_not_delete_other_users(self, notif_service):
        notif_service.create("user-1", "todo-1", "reminder", "msg")
        notif_service.create("user-2", "todo-2", "reminder", "msg")
        notif_service.clear_all("user-1")
        notifications, _ = notif_service.list_for_user("user-2")
        assert len(notifications) == 1

    def test_no_op_when_empty(self, notif_service):
        # Should not raise
        notif_service.clear_all("user-1")
```

---

## Run Unit Tests

### 1. Install Test Dependencies
```bash
pip install pytest httpx
```

### 2. Execute All Unit Tests
```bash
cd backend
python -m pytest tests/ -v
```

### 3. Run Only Unit 1 Tests
```bash
cd backend
python -m pytest tests/test_notification_service.py -v
```

### 4. Run Only Unit 2 Tests
```bash
cd backend
python -m pytest tests/test_reminder_checker.py tests/test_todo_service_reminder.py -v
```

### 5. Expected Results
- **test_reminder_checker.py**: 13 tests pass
- **test_todo_service_reminder.py**: 5 tests pass
- **test_notification_service.py**: 21 tests pass
- **Total**: 39 tests, 0 failures

### 6. Fix Failing Tests
1. Review test output for assertion errors
2. Verify `JSONStore` writes are atomic and reads return latest
3. Verify datetime parsing handles both `Z` suffix and `+00:00` offset
4. Rerun tests until all pass
