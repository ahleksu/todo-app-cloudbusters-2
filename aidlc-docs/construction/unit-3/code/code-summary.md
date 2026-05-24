# Code Summary — Unit 3: Notification Bell UI

## Files Created

### frontend/composables/useNotifications.ts
- Singleton-pattern composable with module-level reactive state (`notifications`, `unreadCount`, `loading`, `error`)
- `fetchNotifications()` — calls `notificationsApi.list()`; suppresses 401 errors during background polling
- `markAsRead(id)` — optimistic update with rollback on failure; recomputes unread count
- `markAllAsRead()` — optimistic update with snapshot rollback; no-op when `unreadCount === 0`
- `clearAll()` — optimistic update with snapshot rollback; no-op when list is empty
- `startPolling()` — idempotent; runs an immediate fetch then polls every 30,000 ms
- `stopPolling()` — clears the interval; safe to call when not polling
- Local `extractErrorMessage()` helper for consistent error UX
- 401 errors during polling are silently ignored to avoid noise during logout

### frontend/components/NotificationPanel.vue
- Dropdown panel with header (title + "Mark all as read" + "Clear all" buttons) and scrollable body
- Loading state, empty state ("No notifications yet"), and notification list
- Per-item: clock icon for `reminder`, alert icon for `overdue`, message, relative time, unread dot
- Unread items are clickable (and keyboard-activatable via Enter/Space) to mark as read
- Read/unread visual distinction (font weight + background tint)
- Dark-mode styles match the rest of the app
- `data-testid` attributes on key interactive elements:
  - `notification-panel-mark-all-read`
  - `notification-panel-clear-all`
  - `notification-panel-loading`
  - `notification-panel-empty`
  - `notification-item-{id}`

### frontend/components/NotificationBell.vue
- Bell icon button in navbar with red unread badge
- Badge shows unread count, capped at "9+" for >9
- Badge hidden when `unreadCount === 0`
- Toggles `NotificationPanel` on click; refetches on open for freshness
- Closes panel on outside click (via document listener + ref containment check)
- Closes panel on Escape key
- Wires panel events to composable actions: `mark-read` → `markAsRead`, `mark-all-read` → `markAllAsRead`, `clear-all` → `clearAll`
- Lifecycle: `startPolling()` on mount; `stopPolling()` on unmount; document listeners removed on unmount
- Accessibility: `aria-haspopup="dialog"`, `aria-expanded`, dynamic `aria-label`
- `data-testid="notification-bell-button"` and `data-testid="notification-bell-badge"`

## Files Modified

### frontend/types/index.ts
- Added `Notification` interface matching Contract 1 response shape exactly:
  - `id`, `user_id`, `todo_id`, `type` (`'reminder' | 'overdue'`), `message`, `is_read`, `created_at`
- Added `NotificationsListResponse` interface (`notifications: Notification[]`, `unread_count: number`)

### frontend/utils/api.ts
- Imported `Notification` and `NotificationsListResponse` types
- Added `notificationsApi` export with 4 methods:
  - `list()` → `GET /notifications` returning `NotificationsListResponse`
  - `markAsRead(id)` → `PATCH /notifications/{id}/read` returning `Notification`
  - `markAllAsRead()` → `POST /notifications/read-all` returning `{ marked_count }`
  - `clearAll()` → `DELETE /notifications` returning `void`

### frontend/pages/dashboard.vue
- Mounted `<NotificationBell />` in the right-side header actions, between `DarkModeToggle` and the Logout button
- No other navbar logic affected

## Contract Compliance

| Contract | Status |
|---|---|
| Contract 1: `GET /api/notifications` (list + unread_count) | ✅ Compliant |
| Contract 1: `PATCH /api/notifications/{id}/read` | ✅ Compliant |
| Contract 1: `POST /api/notifications/read-all` returns `{ marked_count }` | ✅ Compliant |
| Contract 1: `DELETE /api/notifications` returns 204 | ✅ Compliant |
| Contract 5: `Notification` TypeScript interface matches spec exactly | ✅ Compliant |
| Contract 5: `NotificationsListResponse` interface matches spec exactly | ✅ Compliant |

## Stories Implemented

| Story | Description | Status |
|---|---|---|
| US-5 | View Notifications via Bell Icon | ✅ |
| US-6 | View Notification Panel | ✅ |
| US-7 | Mark Notification as Read | ✅ |
| US-8 | Mark All as Read | ✅ |
| US-9 | Clear All Notifications | ✅ |
| US-10 | Automatic 30-second Polling | ✅ |

## Acceptance Criteria

| Criterion | Status |
|---|---|
| Bell icon visible in navbar | ✅ |
| Badge shows unread count (hidden when 0) | ✅ |
| Panel opens on bell click, closes on outside click / Escape | ✅ |
| Notifications display type icon, message, relative time | ✅ |
| Read/unread visual distinction | ✅ |
| Mark as read updates UI optimistically | ✅ |
| Mark all as read clears badge | ✅ |
| Clear all empties panel | ✅ |
| Polling starts on mount, stops on unmount | ✅ |
| Accessible (aria-labels, keyboard navigation) | ✅ |
| Notification TypeScript interface matches Contract 1 exactly | ✅ |

## Validation
- TypeScript diagnostics: 0 errors across all 6 files
- Vue SFC diagnostics: 0 errors
- Auto-imports relied upon (Nuxt convention): `ref`, `computed`, `onMounted`, `onBeforeUnmount`
