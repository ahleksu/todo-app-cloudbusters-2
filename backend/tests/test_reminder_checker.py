"""Unit tests for reminder_checker.check_user() function."""

from datetime import date, datetime, timedelta, timezone

from services.reminder_checker import check_user


# ---------- Reminder detection ----------


def test_detects_due_reminder():
    past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    todos = [
        {
            "id": "todo-1",
            "user_id": "user-1",
            "title": "Buy groceries",
            "status": "pending",
            "due_date": None,
            "reminder_at": past_time,
        }
    ]
    assert check_user("user-1", todos, []) == [
        ("todo-1", "reminder", "Reminder: Buy groceries")
    ]


def test_skips_future_reminder():
    future_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    todos = [
        {
            "id": "todo-1",
            "user_id": "user-1",
            "title": "Buy groceries",
            "status": "pending",
            "due_date": None,
            "reminder_at": future_time,
        }
    ]
    assert check_user("user-1", todos, []) == []


def test_skips_done_todo_reminder():
    past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    todos = [
        {
            "id": "todo-1",
            "user_id": "user-1",
            "title": "Buy groceries",
            "status": "done",
            "due_date": None,
            "reminder_at": past_time,
        }
    ]
    assert check_user("user-1", todos, []) == []


def test_skips_existing_reminder_notification():
    past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    todos = [
        {
            "id": "todo-1",
            "user_id": "user-1",
            "title": "Buy groceries",
            "status": "pending",
            "due_date": None,
            "reminder_at": past_time,
        }
    ]
    existing = [
        {
            "id": "n1",
            "user_id": "user-1",
            "todo_id": "todo-1",
            "type": "reminder",
            "is_read": False,
        }
    ]
    assert check_user("user-1", todos, existing) == []


def test_skips_null_reminder_at():
    todos = [
        {
            "id": "todo-1",
            "user_id": "user-1",
            "title": "Buy groceries",
            "status": "pending",
            "due_date": None,
            "reminder_at": None,
        }
    ]
    assert check_user("user-1", todos, []) == []


# ---------- Overdue detection ----------


def test_detects_overdue_todo():
    past_date = (date.today() - timedelta(days=1)).isoformat()
    todos = [
        {
            "id": "todo-1",
            "user_id": "user-1",
            "title": "Submit report",
            "status": "pending",
            "due_date": past_date,
            "reminder_at": None,
        }
    ]
    assert check_user("user-1", todos, []) == [
        ("todo-1", "overdue", "Overdue: Submit report")
    ]


def test_skips_future_due_date():
    future_date = (date.today() + timedelta(days=1)).isoformat()
    todos = [
        {
            "id": "todo-1",
            "user_id": "user-1",
            "title": "Submit report",
            "status": "pending",
            "due_date": future_date,
            "reminder_at": None,
        }
    ]
    assert check_user("user-1", todos, []) == []


def test_skips_today_due_date():
    today_str = date.today().isoformat()
    todos = [
        {
            "id": "todo-1",
            "user_id": "user-1",
            "title": "Submit report",
            "status": "pending",
            "due_date": today_str,
            "reminder_at": None,
        }
    ]
    assert check_user("user-1", todos, []) == []


def test_skips_done_todo_overdue():
    past_date = (date.today() - timedelta(days=1)).isoformat()
    todos = [
        {
            "id": "todo-1",
            "user_id": "user-1",
            "title": "Submit report",
            "status": "done",
            "due_date": past_date,
            "reminder_at": None,
        }
    ]
    assert check_user("user-1", todos, []) == []


def test_skips_existing_overdue_notification():
    past_date = (date.today() - timedelta(days=1)).isoformat()
    todos = [
        {
            "id": "todo-1",
            "user_id": "user-1",
            "title": "Submit report",
            "status": "pending",
            "due_date": past_date,
            "reminder_at": None,
        }
    ]
    existing = [
        {
            "id": "n1",
            "user_id": "user-1",
            "todo_id": "todo-1",
            "type": "overdue",
            "is_read": False,
        }
    ]
    assert check_user("user-1", todos, existing) == []


# ---------- Combined scenarios ----------


def test_detects_both_reminder_and_overdue():
    past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    past_date = (date.today() - timedelta(days=1)).isoformat()
    todos = [
        {
            "id": "todo-1",
            "user_id": "user-1",
            "title": "Submit report",
            "status": "pending",
            "due_date": past_date,
            "reminder_at": past_time,
        }
    ]
    results = check_user("user-1", todos, [])
    assert {r[1] for r in results} == {"reminder", "overdue"}


def test_empty_todos_list():
    assert check_user("user-1", [], []) == []


def test_handles_invalid_datetime_gracefully():
    todos = [
        {
            "id": "todo-1",
            "user_id": "user-1",
            "title": "Bad date",
            "status": "pending",
            "due_date": "not-a-date",
            "reminder_at": "not-a-datetime",
        }
    ]
    assert check_user("user-1", todos, []) == []
