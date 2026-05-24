"""Unit tests for NotificationService (Unit 1)."""

import pytest

from exceptions import NotFoundError
from services.notification_service import NotificationService
from store import JSONStore


@pytest.fixture
def notif_service(tmp_path):
    return NotificationService(JSONStore(str(tmp_path / "notifications.json")))


# ---------- create() ----------


def test_creates_notification(notif_service):
    n = notif_service.create("user-1", "todo-1", "reminder", "Reminder: Buy groceries")
    assert n.user_id == "user-1"
    assert n.todo_id == "todo-1"
    assert n.type.value == "reminder"
    assert n.message == "Reminder: Buy groceries"
    assert n.is_read is False
    assert n.id
    assert n.created_at is not None


def test_creates_overdue_notification(notif_service):
    n = notif_service.create("user-1", "todo-1", "overdue", "Overdue: Submit report")
    assert n.type.value == "overdue"


def test_create_does_not_dedup(notif_service):
    """create() does NOT dedup by itself — caller's responsibility."""
    notif_service.create("user-1", "todo-1", "reminder", "msg")
    notif_service.create("user-1", "todo-1", "reminder", "msg")
    notifications, _ = notif_service.list_for_user("user-1")
    assert len(notifications) == 2


# ---------- exists() ----------


def test_exists_returns_true_when_match(notif_service):
    notif_service.create("user-1", "todo-1", "reminder", "msg")
    assert notif_service.exists("user-1", "todo-1", "reminder") is True


def test_exists_returns_false_when_no_match(notif_service):
    assert notif_service.exists("user-1", "todo-1", "reminder") is False


def test_exists_distinguishes_user_id(notif_service):
    notif_service.create("user-1", "todo-1", "reminder", "msg")
    assert notif_service.exists("user-2", "todo-1", "reminder") is False


def test_exists_distinguishes_todo_id(notif_service):
    notif_service.create("user-1", "todo-1", "reminder", "msg")
    assert notif_service.exists("user-1", "todo-2", "reminder") is False


def test_exists_distinguishes_type(notif_service):
    notif_service.create("user-1", "todo-1", "reminder", "msg")
    assert notif_service.exists("user-1", "todo-1", "overdue") is False


# ---------- list_for_user() ----------


def test_list_returns_empty_for_no_notifications(notif_service):
    notifications, count = notif_service.list_for_user("user-1")
    assert notifications == []
    assert count == 0


def test_list_returns_only_users_notifications(notif_service):
    notif_service.create("user-1", "todo-1", "reminder", "msg-1")
    notif_service.create("user-2", "todo-2", "reminder", "msg-2")
    notifications, _ = notif_service.list_for_user("user-1")
    assert len(notifications) == 1
    assert notifications[0].user_id == "user-1"


def test_unread_count_reflects_full_unread_count(notif_service):
    """List is capped at 20 but unread_count is the FULL count."""
    for i in range(25):
        notif_service.create("user-1", f"todo-{i}", "reminder", f"msg-{i}")
    notifications, unread_count = notif_service.list_for_user("user-1")
    assert len(notifications) == 20
    assert unread_count == 25


def test_orders_desc_by_created_at(notif_service):
    n1 = notif_service.create("user-1", "todo-1", "reminder", "first")
    n2 = notif_service.create("user-1", "todo-2", "reminder", "second")
    n3 = notif_service.create("user-1", "todo-3", "reminder", "third")
    notifications, _ = notif_service.list_for_user("user-1")
    # Most recently created appears first
    assert notifications[0].id == n3.id
    assert notifications[-1].id == n1.id
    # Middle position
    assert notifications[1].id == n2.id


def test_unread_count_excludes_read(notif_service):
    n = notif_service.create("user-1", "todo-1", "reminder", "msg")
    notif_service.create("user-1", "todo-2", "reminder", "msg")
    notif_service.mark_as_read("user-1", n.id)
    _, unread_count = notif_service.list_for_user("user-1")
    assert unread_count == 1


# ---------- mark_as_read() ----------


def test_marks_notification_read(notif_service):
    n = notif_service.create("user-1", "todo-1", "reminder", "msg")
    updated = notif_service.mark_as_read("user-1", n.id)
    assert updated.is_read is True


def test_mark_as_read_raises_not_found_for_missing(notif_service):
    with pytest.raises(NotFoundError):
        notif_service.mark_as_read("user-1", "missing-id")


def test_mark_as_read_raises_not_found_for_other_user(notif_service):
    n = notif_service.create("user-1", "todo-1", "reminder", "msg")
    with pytest.raises(NotFoundError):
        notif_service.mark_as_read("user-2", n.id)


# ---------- mark_all_as_read() ----------


def test_marks_all_unread(notif_service):
    notif_service.create("user-1", "todo-1", "reminder", "msg")
    notif_service.create("user-1", "todo-2", "reminder", "msg")
    notif_service.create("user-1", "todo-3", "overdue", "msg")
    marked = notif_service.mark_all_as_read("user-1")
    assert marked == 3


def test_returns_zero_when_all_already_read(notif_service):
    n = notif_service.create("user-1", "todo-1", "reminder", "msg")
    notif_service.mark_as_read("user-1", n.id)
    marked = notif_service.mark_all_as_read("user-1")
    assert marked == 0


def test_does_not_affect_other_users(notif_service):
    notif_service.create("user-1", "todo-1", "reminder", "msg")
    notif_service.create("user-2", "todo-2", "reminder", "msg")
    marked = notif_service.mark_all_as_read("user-1")
    assert marked == 1
    _, u2_unread = notif_service.list_for_user("user-2")
    assert u2_unread == 1


# ---------- clear_all() ----------


def test_clear_deletes_all_users_notifications(notif_service):
    notif_service.create("user-1", "todo-1", "reminder", "msg")
    notif_service.create("user-1", "todo-2", "overdue", "msg")
    notif_service.clear_all("user-1")
    notifications, count = notif_service.list_for_user("user-1")
    assert notifications == []
    assert count == 0


def test_clear_does_not_delete_other_users(notif_service):
    notif_service.create("user-1", "todo-1", "reminder", "msg")
    notif_service.create("user-2", "todo-2", "reminder", "msg")
    notif_service.clear_all("user-1")
    notifications, _ = notif_service.list_for_user("user-2")
    assert len(notifications) == 1


def test_clear_no_op_when_empty(notif_service):
    # Should not raise
    notif_service.clear_all("user-1")
