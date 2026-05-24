# Integration Test Instructions — Reminders & Notifications

This document covers integration tests for both **Unit 2 (Reminder Trigger Logic)** and **Unit 1 (Notification Backend)**, plus the cross-unit flow.

## Setup

### 1. Start Backend Server
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 2. Clean Test Data (Optional)
```bash
echo "[]" > backend/data/todos.json
echo "[]" > backend/data/notifications.json
echo "[]" > backend/data/users.json
```

### 3. Register a Test User and Capture Cookie
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"password123","password_confirm":"password123"}'

curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"email":"test@example.com","password":"password123"}'
```

---

## Unit 2 Scenarios (Todo + reminder_at)

### Scenario 2.1: Create Todo with reminder_at
```bash
curl -X POST http://localhost:8000/api/todos \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"title":"Buy groceries","reminder_at":"2026-05-25T09:00:00Z"}'
```
**Expected**: 201; response includes `"reminder_at": "2026-05-25T09:00:00Z"` (or equivalent ISO).

### Scenario 2.2: Update Todo to set reminder_at
```bash
curl -X PUT http://localhost:8000/api/todos/{todo_id} \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"reminder_at":"2026-06-01T10:00:00Z"}'
```
**Expected**: 200; response includes updated `reminder_at`.

### Scenario 2.3: Update Todo to clear reminder_at
```bash
curl -X PUT http://localhost:8000/api/todos/{todo_id} \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"reminder_at":null}'
```
**Expected**: 200; response includes `"reminder_at": null`.

### Scenario 2.4: Create Todo with invalid reminder_at
```bash
curl -X POST http://localhost:8000/api/todos \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"title":"Bad reminder","reminder_at":"not-a-date"}'
```
**Expected**: 422; error mentions invalid datetime format.

### Scenario 2.5: GET /api/todos returns reminder_at
```bash
curl -X GET http://localhost:8000/api/todos -b cookies.txt
```
**Expected**: 200; each todo includes `reminder_at` field (null or ISO).

### Scenario 2.6: Existing todos without reminder_at still work
With existing pre-Unit-2 data in `data/todos.json`:
```bash
curl -X GET http://localhost:8000/api/todos -b cookies.txt
```
**Expected**: 200; existing todos return `reminder_at: null`.

---

## Unit 1 Scenarios (Notifications API)

### Scenario 1.1: Empty state
```bash
curl -X GET http://localhost:8000/api/notifications -b cookies.txt
```
**Expected**: 200; body `{"notifications": [], "unread_count": 0}` (assuming the user has no overdue/due-reminder todos).

### Scenario 1.2: GET triggers reminder detection
```bash
# Create a todo with a past reminder_at
curl -X POST http://localhost:8000/api/todos \
  -H "Content-Type: application/json" -b cookies.txt \
  -d '{"title":"Buy milk","reminder_at":"2020-01-01T00:00:00Z"}'

# Poll notifications endpoint
curl -X GET http://localhost:8000/api/notifications -b cookies.txt
```
**Expected**: 200; body contains a notification of `type: "reminder"` for the new todo, and `unread_count >= 1`.

### Scenario 1.3: GET dedups across polls
```bash
curl -X GET http://localhost:8000/api/notifications -b cookies.txt   # first poll
curl -X GET http://localhost:8000/api/notifications -b cookies.txt   # second poll
```
**Expected**: Both polls return the SAME number of notifications. The reminder for the same todo is NOT duplicated.

### Scenario 1.4: Overdue detection
```bash
# Create a todo with past due_date
curl -X POST http://localhost:8000/api/todos \
  -H "Content-Type: application/json" -b cookies.txt \
  -d '{"title":"Submit report","due_date":"2020-01-01"}'

curl -X GET http://localhost:8000/api/notifications -b cookies.txt
```
**Expected**: 200; body contains a notification of `type: "overdue"` for the new todo.

### Scenario 1.5: Mark single notification as read
```bash
# Use a notification id from a previous GET response
curl -X PATCH http://localhost:8000/api/notifications/{notification_id}/read -b cookies.txt
```
**Expected**: 200; response is the Notification with `"is_read": true`.

### Scenario 1.6: Mark all as read
```bash
curl -X POST http://localhost:8000/api/notifications/read-all -b cookies.txt
```
**Expected**: 200; response `{"marked_count": N}` where N is the number of newly marked notifications.

### Scenario 1.7: Calling read-all again returns 0
```bash
curl -X POST http://localhost:8000/api/notifications/read-all -b cookies.txt
```
**Expected**: 200; response `{"marked_count": 0}`.

### Scenario 1.8: Clear all
```bash
curl -X DELETE http://localhost:8000/api/notifications -b cookies.txt -i
```
**Expected**: 204 No Content.

```bash
curl -X GET http://localhost:8000/api/notifications -b cookies.txt
```
**Expected**: 200; `notifications: []`, `unread_count: 0`.

### Scenario 1.9: 401 on unauthenticated requests
```bash
curl -X GET http://localhost:8000/api/notifications -i
```
**Expected**: 401.

### Scenario 1.10: 404 on mark-as-read for non-existent / not-owned
```bash
curl -X PATCH http://localhost:8000/api/notifications/non-existent-id/read -b cookies.txt -i
```
**Expected**: 404.

### Scenario 1.11: Per-user scoping
```bash
# Register and login a second user (capture cookies-2.txt)
# As user 1, create a todo with past reminder, then poll notifications.
# As user 2, GET /api/notifications using cookies-2.txt.
```
**Expected**: User 2 sees zero notifications belonging to User 1.

---

## Cross-Unit Flow (Unit 1 + Unit 2)

### Scenario X.1: End-to-end reminder lifecycle
1. Register and login (cookies.txt).
2. Create a todo with `reminder_at` 1 minute in the future:
   ```bash
   curl -X POST http://localhost:8000/api/todos -H "Content-Type: application/json" -b cookies.txt \
     -d '{"title":"Test reminder","reminder_at":"<UTC iso 1 minute from now>"}'
   ```
3. Wait 70 seconds.
4. Poll `GET /api/notifications`. **Expected**: A new reminder notification appears, `unread_count` increments.
5. Poll again. **Expected**: Same count (no duplicate).
6. Mark all as read. Poll. **Expected**: `unread_count: 0` but the notification still appears in the list.
7. DELETE `/api/notifications`. Poll. **Expected**: Empty list, `unread_count: 0`.

### Scenario X.2: Marking todo done does not delete past notifications
1. Create a todo with past `reminder_at`.
2. Poll `GET /api/notifications`. **Expected**: reminder notification exists.
3. Mark the todo as done via `PUT /api/todos/{id}` with `{"status":"done"}`.
4. Poll again. **Expected**: existing notification still present (it was already created); no NEW notification is created.

---

## Cleanup
```bash
# Stop server (Ctrl+C)
rm -f cookies.txt cookies-2.txt
```
