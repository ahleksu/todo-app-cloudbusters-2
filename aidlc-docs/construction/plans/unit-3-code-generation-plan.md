# Code Generation Plan — Unit 3: Notification Bell UI

## Unit Context

**Unit**: Unit 3 — Notification Bell UI
**Responsibility**: The bell icon in the navbar, unread count badge, and dropdown panel showing recent notifications with read/clear actions. Polls the backend every 30 seconds.

**Stories Implemented**:
- US-5: View Notifications via Bell Icon (bell + unread count badge)
- US-6: View Notification Panel (dropdown with notification list)
- US-7: Mark Notification as Read (UI + API call)
- US-8: Mark All as Read (UI + API call)
- US-9: Clear All Notifications (UI + API call)
- US-10: Automatic Polling (30-second interval)

**Dependencies**:
- Unit 1's HTTP API contracts (Contract 1 / Contract 5 in `unit-of-work-dependency.md`):
  - `GET /api/notifications`
  - `PATCH /api/notifications/{id}/read`
  - `POST /api/notifications/read-all`
  - `DELETE /api/notifications`

**Files to Create / Modify**:
| File | Action | Description |
|---|---|---|
| `frontend/types/index.ts` | Modify | Add `Notification` and `NotificationsListResponse` interfaces |
| `frontend/utils/api.ts` | Modify | Add `notificationsApi` object (4 methods) |
| `frontend/composables/useNotifications.ts` | Create | State management + 30s polling logic |
| `frontend/components/NotificationPanel.vue` | Create | Dropdown panel listing notifications with actions |
| `frontend/components/NotificationBell.vue` | Create | Bell icon + unread badge + panel toggle |
| `frontend/pages/dashboard.vue` | Modify | Mount NotificationBell into the navbar |

---

## Execution Steps

### Step 1: Modify `frontend/types/index.ts` — Add Notification interfaces
- [x] Add `Notification` interface matching Contract 1 response shape:
  - `id: string`
  - `user_id: string`
  - `todo_id: string`
  - `type: 'reminder' | 'overdue'`
  - `message: string`
  - `is_read: boolean`
  - `created_at: string`
- [x] Add `NotificationsListResponse` interface:
  - `notifications: Notification[]`
  - `unread_count: number`

### Step 2: Modify `frontend/utils/api.ts` — Add notificationsApi
- [x] Import `Notification` and `NotificationsListResponse` types
- [x] Add `notificationsApi` export with 4 methods:
  - `list(): Promise<NotificationsListResponse>` → `GET /notifications`
  - `markAsRead(id: string): Promise<Notification>` → `PATCH /notifications/{id}/read`
  - `markAllAsRead(): Promise<{ marked_count: number }>` → `POST /notifications/read-all`
  - `clearAll(): Promise<void>` → `DELETE /notifications`

### Step 3: Create `frontend/composables/useNotifications.ts` — State + polling
- [x] Module-level reactive state (singleton pattern, like `useToast`):
  - `notifications: Ref<Notification[]>`
  - `unreadCount: Ref<number>`
  - `loading: Ref<boolean>`
  - `error: Ref<string | null>`
- [x] `fetchNotifications()` — calls `notificationsApi.list()`, updates state
- [x] `markAsRead(id)` — optimistic update; rollback on error
- [x] `markAllAsRead()` — optimistic update; rollback on error
- [x] `clearAll()` — optimistic update; rollback on error
- [x] `startPolling()` — initial fetch + `setInterval` every 30,000 ms; idempotent (no double timers)
- [x] `stopPolling()` — clears interval
- [x] Local `extractErrorMessage` helper for consistent error UX
- [x] Export composable function returning state + actions

### Step 4: Create `frontend/components/NotificationPanel.vue` — Dropdown panel
- [x] Props: `notifications: Notification[]`, `unreadCount: number`, `loading: boolean`
- [x] Emits: `mark-read` (id), `mark-all-read`, `clear-all`, `close`
- [x] Header section: title "Notifications", "Mark all as read" button (disabled when `unreadCount === 0`), "Clear all" button (disabled when notifications empty)
- [x] Body: loading skeleton, empty state ("No notifications yet"), or list
- [x] Each notification item:
  - Type icon (clock for `reminder`, alert for `overdue`)
  - Message text
  - Relative time (e.g., "5 minutes ago") via local helper
  - Unread visual indicator (bold + dot or background tint)
  - Click marks as read (emits `mark-read` with id) when unread
- [x] Dark-mode styles consistent with existing components
- [x] `data-testid` attributes on interactive elements (e.g., `notification-panel-mark-all-read`, `notification-panel-clear-all`, `notification-item-{id}`)

### Step 5: Create `frontend/components/NotificationBell.vue` — Bell + badge + panel
- [x] Use `useNotifications()` composable
- [x] Bell icon button in navbar with `aria-label="Notifications"`
- [x] Unread count badge (red circle) — hidden when `unreadCount === 0`; cap display at "9+" if > 9
- [x] Toggles `NotificationPanel` open/closed on click
- [x] Closes panel on outside click (using a ref + global click listener) and on Escape key
- [x] Wires panel events to composable actions: `mark-read` → `markAsRead`, `mark-all-read` → `markAllAsRead`, `clear-all` → `clearAll`
- [x] Calls `startPolling()` on mount and `stopPolling()` on unmount
- [x] `data-testid="notification-bell-button"` and `data-testid="notification-bell-badge"`
- [x] Accessible: `aria-haspopup`, `aria-expanded`, focus management

### Step 6: Modify `frontend/pages/dashboard.vue` — Mount bell in navbar
- [x] Place `<NotificationBell />` in the right-side actions of the header, between `DarkModeToggle` and the Logout button
- [x] Verify no other navbar logic is affected

### Step 7: Generate code summary documentation
- [x] Create `aidlc-docs/construction/unit-3/code/code-summary.md` covering:
  - Files created and modified
  - Contract compliance table
  - Stories implemented table

---

## Acceptance Criteria Verification (from `unit-of-work-story-map.md`)
- [x] Bell icon visible in navbar
- [x] Badge shows unread count (hidden when 0)
- [x] Panel opens on bell click, closes on outside click / Escape
- [x] Notifications display type icon, message, relative time
- [x] Read/unread visual distinction
- [x] Mark as read updates UI optimistically
- [x] Mark all as read clears badge
- [x] Clear all empties panel
- [x] Polling starts on mount, stops on unmount
- [x] Accessible (aria-labels, keyboard navigation)
- [x] Notification TypeScript interface matches Contract 1 exactly

---

## Contract Compliance Targets
- Contract 1: `GET /api/notifications` — consumed by `notificationsApi.list()`
- Contract 1: `PATCH /api/notifications/{id}/read` — consumed by `notificationsApi.markAsRead()`
- Contract 1: `POST /api/notifications/read-all` — consumed by `notificationsApi.markAllAsRead()`
- Contract 1: `DELETE /api/notifications` — consumed by `notificationsApi.clearAll()`
- Contract 5: TypeScript `Notification` and `NotificationsListResponse` interfaces match spec exactly
