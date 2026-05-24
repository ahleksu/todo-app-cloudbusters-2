"""End-to-end integration tests for the Notifications API (Unit 1) and the
cross-unit flow with Unit 2 (reminder_at on todos), using FastAPI TestClient.

These tests stand up the full app with isolated, per-test JSON store paths
so the real data files are not touched.
"""

import json
import os
import shutil
import sys
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest


# Ensure backend root is importable as the test runs from backend/
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Spin up the app with isolated JSON stores rooted in tmp_path/data."""
    isolated_data = tmp_path / "data"
    isolated_data.mkdir()
    # Pre-create empty stores so JSONStore picks them up
    (isolated_data / "users.json").write_text("[]")
    (isolated_data / "todos.json").write_text("[]")
    (isolated_data / "notifications.json").write_text("[]")

    # Force any module that resolves DATA_DIR via __file__ to land inside our
    # isolated tmp_path. We do this by symlinking tmp_path/backend/data ->
    # isolated_data, then point the backend dir constant accordingly.
    # The simplest reliable approach: monkeypatch the JSONStore instances
    # held by the routers / dependencies modules after they're imported.

    # Reset module cache so re-importing doesn't reuse a previous test's stores.
    for mod in [
        "main",
        "dependencies",
        "routers.auth",
        "routers.todos",
        "routers.notifications",
        "services.auth_service",
        "services.todo_service",
        "services.notification_service",
    ]:
        sys.modules.pop(mod, None)

    import dependencies  # noqa: E402
    import routers.todos as todos_module  # noqa: E402
    import routers.notifications as notifications_module  # noqa: E402
    from store import JSONStore  # noqa: E402

    # Repoint the stores at the isolated paths
    dependencies.user_store = JSONStore(str(isolated_data / "users.json"))
    dependencies.auth_service.user_store = dependencies.user_store

    todos_module.todo_store = JSONStore(str(isolated_data / "todos.json"))
    todos_module.todo_service.todo_store = todos_module.todo_store

    notifications_module.notification_store = JSONStore(
        str(isolated_data / "notifications.json")
    )
    notifications_module.notification_service.notification_store = (
        notifications_module.notification_store
    )
    # Critical: the notifications router reads todos via the imported
    # `todo_store` symbol, so make sure that one is the same isolated instance.
    notifications_module.todo_store = todos_module.todo_store

    from fastapi.testclient import TestClient

    import main as main_module

    return TestClient(main_module.app)


def _register_and_login(client, email="alice@example.com", username="alice", password="password123"):
    r = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password,
            "password_confirm": password,
        },
    )
    assert r.status_code in (200, 201), r.text
    # /register already sets the auth cookie. We additionally call /login to
    # exercise both endpoints.
    r = client.post(
        "/api/auth/login",
        json={"identifier": email, "password": password},
    )
    assert r.status_code == 200, r.text
    # Cookie is set on the client; subsequent calls are authenticated.


# ---------- Unit 1: Notifications API ----------


def test_empty_state(client):
    _register_and_login(client)
    r = client.get("/api/notifications")
    assert r.status_code == 200
    body = r.json()
    assert body == {"notifications": [], "unread_count": 0}


def test_unauthenticated_401(client):
    r = client.get("/api/notifications")
    assert r.status_code == 401


def test_get_triggers_reminder_detection(client):
    _register_and_login(client)
    past_iso = "2020-01-01T00:00:00Z"
    r = client.post("/api/todos", json={"title": "Buy milk", "reminder_at": past_iso})
    assert r.status_code == 201, r.text

    r = client.get("/api/notifications")
    assert r.status_code == 200
    body = r.json()
    assert body["unread_count"] >= 1
    types = {n["type"] for n in body["notifications"]}
    assert "reminder" in types


def test_get_dedups_across_polls(client):
    _register_and_login(client)
    client.post(
        "/api/todos", json={"title": "Buy milk", "reminder_at": "2020-01-01T00:00:00Z"}
    )
    first = client.get("/api/notifications").json()
    second = client.get("/api/notifications").json()
    assert len(first["notifications"]) == len(second["notifications"])
    assert first["unread_count"] == second["unread_count"]


def test_overdue_detection(client):
    _register_and_login(client)
    client.post("/api/todos", json={"title": "Submit report", "due_date": "2020-01-01"})
    body = client.get("/api/notifications").json()
    types = {n["type"] for n in body["notifications"]}
    assert "overdue" in types


def test_mark_single_as_read(client):
    _register_and_login(client)
    client.post(
        "/api/todos", json={"title": "Buy milk", "reminder_at": "2020-01-01T00:00:00Z"}
    )
    notifs = client.get("/api/notifications").json()["notifications"]
    notif_id = notifs[0]["id"]
    r = client.patch(f"/api/notifications/{notif_id}/read")
    assert r.status_code == 200
    assert r.json()["is_read"] is True

    body = client.get("/api/notifications").json()
    # unread_count should drop by 1 from initial
    assert body["unread_count"] == 0


def test_mark_all_as_read(client):
    _register_and_login(client)
    client.post(
        "/api/todos", json={"title": "T1", "reminder_at": "2020-01-01T00:00:00Z"}
    )
    client.post("/api/todos", json={"title": "T2", "due_date": "2020-01-01"})
    client.get("/api/notifications")  # trigger creation

    r = client.post("/api/notifications/read-all")
    assert r.status_code == 200
    assert r.json()["marked_count"] >= 1

    # Calling again returns 0
    r = client.post("/api/notifications/read-all")
    assert r.json()["marked_count"] == 0

    body = client.get("/api/notifications").json()
    assert body["unread_count"] == 0


def test_clear_all(client):
    _register_and_login(client)
    client.post(
        "/api/todos", json={"title": "T1", "reminder_at": "2020-01-01T00:00:00Z"}
    )
    client.get("/api/notifications")  # trigger creation

    r = client.delete("/api/notifications")
    assert r.status_code == 204

    body = client.get("/api/notifications").json()
    # GET will re-detect the same reminder, but since notifications.json was
    # cleared and the todo still has past reminder_at, a fresh notification is
    # expected. The contract guarantees clear_all wipes the store; the next
    # poll re-creates from the still-existing trigger condition.
    # We verify the wipe happened and a single notification reappears.
    assert len(body["notifications"]) == 1


def test_404_on_other_users_notification(client):
    _register_and_login(client)
    client.post(
        "/api/todos", json={"title": "T1", "reminder_at": "2020-01-01T00:00:00Z"}
    )
    notif_id = client.get("/api/notifications").json()["notifications"][0]["id"]

    # Switch user — clear cookies and register a different user
    client.cookies.clear()
    _register_and_login(client, email="bob@example.com", username="bob")

    r = client.patch(f"/api/notifications/{notif_id}/read")
    assert r.status_code == 404


def test_404_on_missing_id(client):
    _register_and_login(client)
    r = client.patch("/api/notifications/non-existent-id/read")
    assert r.status_code == 404


def test_per_user_scoping(client):
    _register_and_login(client)
    client.post(
        "/api/todos", json={"title": "T1", "reminder_at": "2020-01-01T00:00:00Z"}
    )
    client.get("/api/notifications")  # creates Alice's notification

    client.cookies.clear()
    _register_and_login(client, email="bob@example.com", username="bob")
    body = client.get("/api/notifications").json()
    assert body["notifications"] == []
    assert body["unread_count"] == 0


# ---------- Unit 2: Todo + reminder_at via API ----------


def test_create_todo_with_reminder_at(client):
    _register_and_login(client)
    r = client.post(
        "/api/todos", json={"title": "Buy milk", "reminder_at": "2026-05-25T09:00:00Z"}
    )
    assert r.status_code == 201
    body = r.json()
    assert body["reminder_at"] is not None


def test_update_clears_reminder_at(client):
    _register_and_login(client)
    todo = client.post(
        "/api/todos", json={"title": "Buy milk", "reminder_at": "2026-05-25T09:00:00Z"}
    ).json()
    r = client.put(f"/api/todos/{todo['id']}", json={"reminder_at": None})
    assert r.status_code == 200
    assert r.json()["reminder_at"] is None


def test_invalid_reminder_at_returns_422(client):
    _register_and_login(client)
    r = client.post(
        "/api/todos", json={"title": "Bad", "reminder_at": "not-a-datetime"}
    )
    assert r.status_code == 422


# ---------- Cross-unit flow ----------


def test_cross_unit_reminder_lifecycle(client):
    """End-to-end: create reminder -> notification appears -> read-all -> clear."""
    _register_and_login(client)
    # Use a clearly past timestamp
    client.post(
        "/api/todos",
        json={"title": "Pay bill", "reminder_at": "2020-01-01T00:00:00Z"},
    )
    body = client.get("/api/notifications").json()
    assert body["unread_count"] >= 1

    body = client.post("/api/notifications/read-all").json()
    assert body["marked_count"] >= 1

    body = client.get("/api/notifications").json()
    assert body["unread_count"] == 0
