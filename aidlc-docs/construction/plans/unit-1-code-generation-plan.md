# Unit 1: Notification Backend — Code Generation Plan

**Unit Name**: Unit 1 — Notification Backend
**Phase**: CONSTRUCTION
**Stage**: Code Generation (Part 1 — Planning) — APPROVED, Part 2 — COMPLETE
**Project Type**: Brownfield
**Workspace Root**: `/Users/johnalexrobles/Desktop/ahleksu/todo-app-cloudbusters-2`

---

## Unit Context

**Responsibility**: Notification data layer and CRUD endpoints. Manages notification storage, retrieval, and state changes. The `GET /api/notifications` endpoint integrates with Unit 2's `reminder_checker.check_user()` to detect new due/overdue notifications on each poll and persist them.

**Stories Implemented** (from `unit-of-work-story-map.md` mapping):
- Receive a reminder notification when a todo's reminder time is reached
- Receive an overdue notification when a todo passes its due date without being completed
- See an unread badge count on the bell icon
- Open a notification panel to view recent notifications
- Mark a single notification as read
- Mark all notifications as read at once
- Clear all notifications
- Notifications must not be duplicated for the same (todo, type) pair
- Notifications are scoped per-user (no cross-user leakage)

**Dependencies**:
- **Unit 2** (already complete): imports `reminder_checker.check_user()` and reads existing todos via the shared `todo_store` instance.

**Files to Create or Modify**:

| File | Action | Description |
|---|---|---|
| `backend/models.py` | Modify | Add `NotificationType` enum, `Notification`, `NotificationsListResponse`, `MarkAllReadResponse` models |
| `backend/services/notification_service.py` | Create | `NotificationService` class with `create()`, `exists()`, `list_for_user()`, `mark_as_read()`, `mark_all_as_read()`, `clear_all()` |
| `backend/routers/notifications.py` | Create | FastAPI router with 4 endpoints; GET endpoint integrates with `reminder_checker.check_user()` |
| `backend/data/notifications.json` | Create | Empty JSON array `[]` |
| `backend/main.py` | Modify | Import and register notifications router |

---

## API Contracts (from `unit-of-work-dependency.md`)

All four HTTP endpoints, exact JSON shapes, and the internal Python contracts (`notification_service.create`, `notification_service.exists`, `reminder_checker.check_user`) are specified in `aidlc-docs/inception/application-design/unit-of-work-dependency.md` Contracts 1, 2, 3.

---

## Generation Steps (with checkboxes)

### Step 1: Models — extend `backend/models.py`
- [x] Add `NotificationType(str, Enum)` with values `REMINDER = "reminder"` and `OVERDUE = "overdue"`
- [x] Add `Notification(BaseModel)` with fields: `id: str`, `user_id: str`, `todo_id: str`, `type: NotificationType`, `message: str`, `is_read: bool = False`, `created_at: datetime`
- [x] Expose `Notification` directly via `response_model=Notification` (matches existing Todo pattern — no separate Response class)
- [x] Add `NotificationsListResponse(BaseModel)` with fields: `notifications: list[Notification]`, `unread_count: int`
- [x] Add `MarkAllReadResponse(BaseModel)` with field: `marked_count: int`

### Step 2: Service — create `backend/services/notification_service.py`
- [x] Class `NotificationService` initialized with `notification_store: JSONStore`
- [x] Method `create(user_id, todo_id, notification_type, message) -> Notification`
- [x] Method `exists(user_id, todo_id, notification_type) -> bool`
- [x] Method `list_for_user(user_id) -> tuple[list[Notification], int]`
- [x] Method `mark_as_read(user_id, notification_id) -> Notification`
- [x] Method `mark_all_as_read(user_id) -> int`
- [x] Method `clear_all(user_id) -> None`

### Step 3: Storage — create `backend/data/notifications.json`
- [x] Empty JSON array `[]` written to `backend/data/notifications.json`

### Step 4: Router — create `backend/routers/notifications.py`
- [x] Initialize `notification_store` and `notification_service`
- [x] Import shared `todo_store` from `routers.todos`
- [x] Import `check_user` from `services.reminder_checker`
- [x] `GET /api/notifications` integrates check_user + persists results + returns NotificationsListResponse
- [x] `PATCH /api/notifications/{notification_id}/read` returns Notification
- [x] `POST /api/notifications/read-all` returns MarkAllReadResponse
- [x] `DELETE /api/notifications` returns 204
- [x] All endpoints use `Depends(get_current_user)`

### Step 5: Main — modify `backend/main.py`
- [x] Added `from routers.notifications import router as notifications_router`
- [x] Added `app.include_router(notifications_router)` after `todos_router`

### Step 6: Documentation — create code summary
- [x] Created `aidlc-docs/construction/unit-1/code/code-summary.md`

---

## Verification

- `python3 -m py_compile` clean for all 4 Python files (models.py, notification_service.py, notifications.py, main.py)
- `getDiagnostics` returns no findings on any file
- All HTTP shapes match Contract 1
- Internal `notification_service.create` and `exists` signatures match Contract 2
- GET handler integrates `reminder_checker.check_user()` per Contract 3

---

**Status**: COMPLETE. Awaiting user approval to proceed to Build and Test.
