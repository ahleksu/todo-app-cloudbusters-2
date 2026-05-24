# Integration Test Instructions — Unit 3: Notification Bell UI

## Purpose
Verify Unit 3 (frontend bell + panel) integrates correctly with Unit 1 (backend notifications API) at runtime.

## Prerequisites
- Backend running on `http://localhost:8000` with Unit 1 endpoints active
- Backend has at least one user account and a todo with a past `reminder_at` and/or past `due_date` (so notifications get generated)
- Frontend running on `http://localhost:3000`

## Setup Integration Test Environment

### 1. Start Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 2. Seed Test Data (curl)
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"u3test@example.com","username":"u3test","password":"password123","password_confirm":"password123"}'

# Login (saves cookie)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" -c cookies.txt \
  -d '{"identifier":"u3test","password":"password123"}'

# Create a todo with a reminder in the past (will trigger reminder notification)
curl -X POST http://localhost:8000/api/todos \
  -H "Content-Type: application/json" -b cookies.txt \
  -d '{"title":"Buy groceries","reminder_at":"2026-05-01T09:00:00Z"}'

# Create a todo with an overdue due_date (will trigger overdue notification)
curl -X POST http://localhost:8000/api/todos \
  -H "Content-Type: application/json" -b cookies.txt \
  -d '{"title":"Submit report","due_date":"2026-05-10"}'
```

### 3. Start Frontend
```bash
cd frontend
npm run dev
```

### 4. Log In Through the UI
Open `http://localhost:3000`, log in as `u3test`, navigate to the dashboard.

---

## Test Scenarios

### Scenario 1: Bell renders in navbar with unread badge

**Steps**:
1. Navigate to `/dashboard`
2. Wait up to 30 seconds for first poll (or refresh — first fetch happens on mount)

**Expected**:
- Bell icon visible in the navbar between dark-mode toggle and Logout button
- Red badge with "2" displayed (one reminder + one overdue)
- `aria-label` reads "Notifications, 2 unread"

---

### Scenario 2: Open and close panel

**Steps**:
1. Click the bell icon
2. Observe the panel opens
3. Click outside the panel
4. Observe the panel closes
5. Click bell again, then press Escape

**Expected**:
- Panel toggles open on click; closes on outside click; closes on Escape
- `aria-expanded` toggles `true`/`false`

---

### Scenario 3: Notification item layout

**Steps**:
1. Open panel
2. Inspect rendered list

**Expected**:
- Two notifications listed, newest first
- Each item shows: type icon (clock for reminder, alert for overdue), message text ("Reminder: Buy groceries", "Overdue: Submit report"), relative time
- Both items rendered as unread (background tint + bold text + dot indicator)

---

### Scenario 4: Mark single notification as read

**Steps**:
1. Open panel
2. Click on the "Reminder: Buy groceries" item

**Expected**:
- Item visually transitions to read state immediately (background tint removed, text un-bolded, dot gone)
- Badge count drops to 1
- Network tab shows `PATCH /api/notifications/{id}/read` returning 200
- After next poll (30s), state remains correct

---

### Scenario 5: Mark all as read

**Steps**:
1. Reset by reopening panel — there should still be unread items
2. Click "Mark all read"

**Expected**:
- All items transition to read state immediately
- Badge disappears (`unreadCount === 0`, badge hidden)
- Network tab shows `POST /api/notifications/read-all` returning 200 with `{ "marked_count": N }`

---

### Scenario 6: Clear all notifications

**Steps**:
1. Click "Clear all"

**Expected**:
- Panel transitions to empty state ("No notifications yet")
- Badge gone
- Network tab shows `DELETE /api/notifications` returning 204

---

### Scenario 7: Polling fires every 30 seconds

**Steps**:
1. Open browser DevTools → Network tab → filter to `notifications`
2. Stay on dashboard for at least 90 seconds

**Expected**:
- A `GET /api/notifications` request fires immediately on dashboard mount
- Subsequent requests fire approximately every 30 seconds (±100 ms)

---

### Scenario 8: Polling stops when leaving dashboard

**Steps**:
1. Note the latest poll request in Network tab
2. Click Logout (navigates to `/login`)
3. Wait 60 seconds

**Expected**:
- No additional `GET /api/notifications` requests fire after logout
- (The backend will return 401 anyway, but no requests should be made)

---

### Scenario 9: Optimistic rollback on failure

**Steps**:
1. Open panel, with at least one unread item
2. In DevTools, set Network throttling to "Offline" or use a request blocker
3. Click an unread item to mark as read
4. Observe brief visual update, then rollback

**Expected**:
- Item briefly appears read, then snaps back to unread when API call fails
- An error message is set in the composable's `error` state (visible if surfaced via toast)

---

### Scenario 10: Empty state

**Steps**:
1. Click "Clear all" until panel is empty
2. Close and reopen the panel

**Expected**:
- "No notifications yet" message displayed with bell icon

---

### Scenario 11: Badge cap "9+"

**Steps**:
1. (Manually) seed 10+ unread notifications via backend or repeated todo manipulation
2. Reload dashboard

**Expected**:
- Badge shows "9+" instead of the literal count
- `aria-label` shows the full count for screen readers (e.g., "Notifications, 12 unread")

---

## Cleanup
```bash
# Stop both servers (Ctrl+C)
rm -f cookies.txt
# Reset backend test data if desired
echo "[]" > backend/data/notifications.json
echo "[]" > backend/data/todos.json
```

## Coverage Mapping

| Story | Scenario(s) |
|---|---|
| US-5: View Notifications via Bell Icon | 1 |
| US-6: View Notification Panel | 2, 3, 10 |
| US-7: Mark Notification as Read | 4, 9 |
| US-8: Mark All as Read | 5 |
| US-9: Clear All Notifications | 6 |
| US-10: Automatic 30-second Polling | 7, 8 |
| Edge: Badge cap at 9+ | 11 |
