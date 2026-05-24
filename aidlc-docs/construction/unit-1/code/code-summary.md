# Unit 1: Notification Backend — Code Summary

**Generated**: 2026-05-24T09:28:47Z
**Plan**: `aidlc-docs/construction/plans/unit-1-code-generation-plan.md`

---

## Files Created

| File | Purpose |
|---|---|
| `backend/services/notification_service.py` | NotificationService class with `create`, `exists`, `list_for_user`, `mark_as_read`, `mark_all_as_read`, `clear_all` |
| `backend/routers/notifications.py` | FastAPI router with 4 endpoints; GET integrates `reminder_checker.check_user()` |
| `backend/data/notifications.json` | Empty JSON array for notification persistence |

## Files Modified

| File | Change |
|---|---|
| `backend/models.py` | Added `NotificationType` enum, `Notification`, `NotificationsListResponse`, `MarkAllReadResponse` models |
| `backend/main.py` | Imported and registered `notifications_router` |

---

## API Endpoints (Contract 1 conformance)

| Method | Path | Status | Body / Response | Notes |
|---|---|---|---|---|
| GET | `/api/notifications` | 200 | `NotificationsListResponse` | Triggers reminder detection on each call; sorted DESC, max 20; `unread_count` is full count |
| PATCH | `/api/notifications/{id}/read` | 200 | `Notification` | 404 if not found or not owned |
| POST | `/api/notifications/read-all` | 200 | `MarkAllReadResponse {marked_count}` | Counts only newly marked (previously unread) |
| DELETE | `/api/notifications` | 204 | (empty) | Clears all of user's notifications |

All endpoints require auth via `Depends(get_current_user)`. 401 is returned for unauthenticated requests through the existing exception handler.

---

## Internal Contracts (Contract 2 conformance)

```python
notification_service.create(user_id: str, todo_id: str, notification_type: str, message: str) -> Notification
notification_service.exists(user_id: str, todo_id: str, notification_type: str) -> bool
```

Both signatures match the contract in `unit-of-work-dependency.md` exactly.

---

## Integration with Unit 2

The GET handler imports and calls Unit 2's `check_user`:

```python
from services.reminder_checker import check_user
new_notifications = check_user(user_id, user_todos, user_notifications)
```

`check_user` is a pure function. The router persists each detected notification via `notification_service.create()`, with a defensive `exists()` check to guard against race conditions across concurrent polls.

---

## Acceptance Criteria — Verification

| Criterion | Status | Evidence |
|---|---|---|
| GET response shape matches Contract 1 | ✅ | `NotificationsListResponse` model fields match exactly |
| PATCH response shape matches Contract 1 | ✅ | Returns `Notification` model |
| POST /read-all returns `{marked_count}` | ✅ | `MarkAllReadResponse` model |
| DELETE returns 204 | ✅ | `status_code=204` on route |
| Per-user scoping enforced | ✅ | All service methods filter by `user_id`; `mark_as_read` raises `NotFoundError` if not owned |
| Deduplication on (user_id, todo_id, type) | ✅ | `exists()` method + `check_user`'s built-in dedup + defensive `exists()` in router |
| `notification_service.create()` signature matches Contract 2 | ✅ | Verified in source |
| `notification_service.exists()` signature matches Contract 2 | ✅ | Verified in source |
| Authentication via httpOnly cookie | ✅ | `Depends(get_current_user)` on all 4 routes |
| 401 on unauthenticated requests | ✅ | Inherited from `get_current_user` raising `UnauthorizedError` |
| Pydantic field names match Contract 1 JSON | ✅ | `id`, `user_id`, `todo_id`, `type`, `message`, `is_read`, `created_at` |
| Notifications ordered DESC by `created_at`, max 20 | ✅ | `list_for_user` sorts then slices `[:20]` |
| `unread_count` is full count (not capped) | ✅ | `unread_count` computed before slicing |
| Atomic writes | ✅ | Reuses existing `JSONStore` (atomic via temp + `os.replace`) |
| Python syntax / import resolution | ✅ | `python3 -m py_compile` passes; getDiagnostics returns clean |

---

## Design Decisions

1. **No separate `NotificationResponse` model.** The existing `Todo` model is exposed directly via `response_model=Todo`. Same pattern for `Notification` rather than introducing a parallel response class.

2. **Defensive `exists()` check in router despite `check_user`'s dedup.** `check_user` is pure and dedupes against the snapshot it was given. If two concurrent polls both pass dedup before either persists, one would create a duplicate. The router's defensive `exists()` check on each create closes that race window for the common case.

3. **`mark_all_as_read` returns count of *newly marked* rows.** Notifications already read are not counted. Matches user expectation that the count reflects the user's action.

4. **`clear_all` writes only on change.** Avoids unnecessary disk writes when called on an empty user state.

5. **Reuse of `todo_store` via import.** The router imports `todo_store` from `routers.todos` instead of constructing a second JSONStore on the same file. Single shared instance, no divergent reads.

---

## Out of Scope

- Frontend bell UI (Unit 3)
- Frontend notification panel (Unit 3)
- Frontend `notificationsApi` client (Unit 3)
- Authoritative testing — covered separately in Build & Test stage
