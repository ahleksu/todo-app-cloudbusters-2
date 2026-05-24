# Unit Test Instructions — Unit 3: Notification Bell UI

## Test Framework
The frontend project does not currently ship a test framework. The instructions below assume Vitest + Vue Test Utils, which is the standard pairing for Nuxt 3 projects. To enable:

```bash
cd frontend
npm i -D vitest @vue/test-utils @vitejs/plugin-vue jsdom @testing-library/vue happy-dom
```

Add a `vitest.config.ts` at the frontend root (or `nuxt.config.ts` test integration) configured for `jsdom` environment with global Nuxt auto-imports stubbed.

If the team prefers Playwright for UI testing instead, see `unit-3-integration-test-instructions.md` for a manual end-to-end approach.

## Test Files to Create

### tests/composables/useNotifications.test.ts

Tests for the polling composable:

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'
import { useNotifications } from '~/composables/useNotifications'

// Mock the api module
vi.mock('~/utils/api', () => ({
  notificationsApi: {
    list: vi.fn(),
    markAsRead: vi.fn(),
    markAllAsRead: vi.fn(),
    clearAll: vi.fn(),
  },
}))

import { notificationsApi } from '~/utils/api'

describe('useNotifications', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('fetchNotifications populates state from API', async () => {
    const sample = {
      notifications: [
        { id: '1', user_id: 'u1', todo_id: 't1', type: 'reminder', message: 'Test', is_read: false, created_at: '2026-05-24T10:00:00Z' },
      ],
      unread_count: 1,
    }
    ;(notificationsApi.list as any).mockResolvedValue(sample)

    const { fetchNotifications, notifications, unreadCount } = useNotifications()
    await fetchNotifications()

    expect(notifications.value).toEqual(sample.notifications)
    expect(unreadCount.value).toBe(1)
  })

  it('markAsRead optimistically updates and recomputes unreadCount', async () => {
    const initial = {
      notifications: [
        { id: '1', user_id: 'u1', todo_id: 't1', type: 'reminder', message: 'A', is_read: false, created_at: '2026-05-24T10:00:00Z' },
        { id: '2', user_id: 'u1', todo_id: 't2', type: 'overdue', message: 'B', is_read: false, created_at: '2026-05-24T09:00:00Z' },
      ],
      unread_count: 2,
    }
    ;(notificationsApi.list as any).mockResolvedValue(initial)
    ;(notificationsApi.markAsRead as any).mockResolvedValue({ ...initial.notifications[0], is_read: true })

    const { fetchNotifications, markAsRead, notifications, unreadCount } = useNotifications()
    await fetchNotifications()
    await markAsRead('1')

    expect(notifications.value.find(n => n.id === '1')?.is_read).toBe(true)
    expect(unreadCount.value).toBe(1)
  })

  it('markAsRead rolls back on API failure', async () => {
    const initial = {
      notifications: [
        { id: '1', user_id: 'u1', todo_id: 't1', type: 'reminder', message: 'A', is_read: false, created_at: '2026-05-24T10:00:00Z' },
      ],
      unread_count: 1,
    }
    ;(notificationsApi.list as any).mockResolvedValue(initial)
    ;(notificationsApi.markAsRead as any).mockRejectedValue(new Error('Network'))

    const { fetchNotifications, markAsRead, notifications, unreadCount, error } = useNotifications()
    await fetchNotifications()
    await markAsRead('1')

    expect(notifications.value[0].is_read).toBe(false)
    expect(unreadCount.value).toBe(1)
    expect(error.value).toBeTruthy()
  })

  it('markAllAsRead is a no-op when unreadCount is 0', async () => {
    const initial = {
      notifications: [
        { id: '1', user_id: 'u1', todo_id: 't1', type: 'reminder', message: 'A', is_read: true, created_at: '2026-05-24T10:00:00Z' },
      ],
      unread_count: 0,
    }
    ;(notificationsApi.list as any).mockResolvedValue(initial)

    const { fetchNotifications, markAllAsRead } = useNotifications()
    await fetchNotifications()
    await markAllAsRead()

    expect(notificationsApi.markAllAsRead).not.toHaveBeenCalled()
  })

  it('clearAll empties list optimistically and rolls back on failure', async () => {
    const initial = {
      notifications: [
        { id: '1', user_id: 'u1', todo_id: 't1', type: 'reminder', message: 'A', is_read: false, created_at: '2026-05-24T10:00:00Z' },
      ],
      unread_count: 1,
    }
    ;(notificationsApi.list as any).mockResolvedValue(initial)
    ;(notificationsApi.clearAll as any).mockRejectedValue(new Error('Server'))

    const { fetchNotifications, clearAll, notifications } = useNotifications()
    await fetchNotifications()
    await clearAll()

    // Rolled back
    expect(notifications.value.length).toBe(1)
  })

  it('startPolling calls fetchNotifications on interval', async () => {
    ;(notificationsApi.list as any).mockResolvedValue({ notifications: [], unread_count: 0 })

    const { startPolling, stopPolling } = useNotifications()
    startPolling()

    // Initial fetch
    expect(notificationsApi.list).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(30_000)
    await Promise.resolve() // flush microtasks

    expect(notificationsApi.list).toHaveBeenCalledTimes(2)

    stopPolling()
  })

  it('startPolling is idempotent', () => {
    ;(notificationsApi.list as any).mockResolvedValue({ notifications: [], unread_count: 0 })

    const { startPolling, stopPolling } = useNotifications()
    startPolling()
    startPolling() // second call should not start a second timer

    vi.advanceTimersByTime(30_000)
    // 1 initial fetch + 1 interval tick = 2; if a second timer were running we'd see 4
    expect(notificationsApi.list).toHaveBeenCalledTimes(2)

    stopPolling()
  })

  it('stopPolling clears the interval', () => {
    ;(notificationsApi.list as any).mockResolvedValue({ notifications: [], unread_count: 0 })

    const { startPolling, stopPolling } = useNotifications()
    startPolling()
    stopPolling()

    vi.advanceTimersByTime(30_000)
    // Only the initial fetch from startPolling
    expect(notificationsApi.list).toHaveBeenCalledTimes(1)
  })
})
```

### tests/components/NotificationBell.test.ts

Tests for the bell button + badge:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import NotificationBell from '~/components/NotificationBell.vue'

vi.mock('~/composables/useNotifications', () => {
  const { ref } = require('vue')
  return {
    useNotifications: () => ({
      notifications: ref([]),
      unreadCount: ref(0),
      loading: ref(false),
      fetchNotifications: vi.fn(),
      markAsRead: vi.fn(),
      markAllAsRead: vi.fn(),
      clearAll: vi.fn(),
      startPolling: vi.fn(),
      stopPolling: vi.fn(),
    }),
  }
})

describe('NotificationBell', () => {
  it('renders the bell button', () => {
    const wrapper = mount(NotificationBell)
    expect(wrapper.find('[data-testid="notification-bell-button"]').exists()).toBe(true)
  })

  it('hides badge when unreadCount is 0', () => {
    const wrapper = mount(NotificationBell)
    expect(wrapper.find('[data-testid="notification-bell-badge"]').exists()).toBe(false)
  })

  it('shows "9+" when unreadCount > 9', async () => {
    // Re-mock with high count for this test
    vi.doMock('~/composables/useNotifications', () => {
      const { ref } = require('vue')
      return {
        useNotifications: () => ({
          notifications: ref([]),
          unreadCount: ref(15),
          loading: ref(false),
          fetchNotifications: vi.fn(),
          markAsRead: vi.fn(),
          markAllAsRead: vi.fn(),
          clearAll: vi.fn(),
          startPolling: vi.fn(),
          stopPolling: vi.fn(),
        }),
      }
    })
    // Re-import after mock change
    const { default: BellWithCount } = await import('~/components/NotificationBell.vue')
    const wrapper = mount(BellWithCount)
    expect(wrapper.find('[data-testid="notification-bell-badge"]').text()).toBe('9+')
  })

  it('toggles panel on click', async () => {
    const wrapper = mount(NotificationBell)
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)

    await wrapper.find('[data-testid="notification-bell-button"]').trigger('click')
    expect(wrapper.find('[role="dialog"]').exists()).toBe(true)
  })
})
```

### tests/components/NotificationPanel.test.ts

Tests for the panel:

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import NotificationPanel from '~/components/NotificationPanel.vue'
import type { Notification } from '~/types'

const sample: Notification[] = [
  { id: '1', user_id: 'u1', todo_id: 't1', type: 'reminder', message: 'Reminder: A', is_read: false, created_at: new Date(Date.now() - 60_000).toISOString() },
  { id: '2', user_id: 'u1', todo_id: 't2', type: 'overdue', message: 'Overdue: B', is_read: true, created_at: new Date(Date.now() - 3_600_000).toISOString() },
]

describe('NotificationPanel', () => {
  it('renders empty state when no notifications', () => {
    const wrapper = mount(NotificationPanel, {
      props: { notifications: [], unreadCount: 0, loading: false },
    })
    expect(wrapper.find('[data-testid="notification-panel-empty"]').exists()).toBe(true)
  })

  it('renders loading state', () => {
    const wrapper = mount(NotificationPanel, {
      props: { notifications: [], unreadCount: 0, loading: true },
    })
    expect(wrapper.find('[data-testid="notification-panel-loading"]').exists()).toBe(true)
  })

  it('renders notification items', () => {
    const wrapper = mount(NotificationPanel, {
      props: { notifications: sample, unreadCount: 1, loading: false },
    })
    expect(wrapper.find('[data-testid="notification-item-1"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="notification-item-2"]').exists()).toBe(true)
  })

  it('disables Mark all read when unreadCount is 0', () => {
    const wrapper = mount(NotificationPanel, {
      props: { notifications: sample, unreadCount: 0, loading: false },
    })
    expect(wrapper.find('[data-testid="notification-panel-mark-all-read"]').attributes('disabled')).toBeDefined()
  })

  it('disables Clear all when notifications is empty', () => {
    const wrapper = mount(NotificationPanel, {
      props: { notifications: [], unreadCount: 0, loading: false },
    })
    expect(wrapper.find('[data-testid="notification-panel-clear-all"]').attributes('disabled')).toBeDefined()
  })

  it('emits mark-read on unread item click', async () => {
    const wrapper = mount(NotificationPanel, {
      props: { notifications: sample, unreadCount: 1, loading: false },
    })
    await wrapper.find('[data-testid="notification-item-1"]').trigger('click')
    expect(wrapper.emitted('mark-read')?.[0]).toEqual(['1'])
  })

  it('does not emit mark-read on already-read item click', async () => {
    const wrapper = mount(NotificationPanel, {
      props: { notifications: sample, unreadCount: 1, loading: false },
    })
    await wrapper.find('[data-testid="notification-item-2"]').trigger('click')
    expect(wrapper.emitted('mark-read')).toBeUndefined()
  })

  it('emits mark-all-read when Mark all read clicked', async () => {
    const wrapper = mount(NotificationPanel, {
      props: { notifications: sample, unreadCount: 1, loading: false },
    })
    await wrapper.find('[data-testid="notification-panel-mark-all-read"]').trigger('click')
    expect(wrapper.emitted('mark-all-read')).toHaveLength(1)
  })

  it('emits clear-all when Clear all clicked', async () => {
    const wrapper = mount(NotificationPanel, {
      props: { notifications: sample, unreadCount: 1, loading: false },
    })
    await wrapper.find('[data-testid="notification-panel-clear-all"]').trigger('click')
    expect(wrapper.emitted('clear-all')).toHaveLength(1)
  })
})
```

## Run Unit Tests

### 1. Install Test Dependencies (one-time)
```bash
cd frontend
npm i -D vitest @vue/test-utils happy-dom
```

### 2. Add Test Script to package.json
```json
"scripts": {
  "test": "vitest run",
  "test:watch": "vitest"
}
```

### 3. Execute All Unit Tests
```bash
cd frontend
npm test
```

### 4. Expected Results
- **useNotifications.test.ts**: 8 tests pass
- **NotificationBell.test.ts**: 4 tests pass
- **NotificationPanel.test.ts**: 8 tests pass
- **Total**: 20 tests, 0 failures

## Notes
- The composable uses module-level singleton state, so tests should clear state between runs (re-import or reset refs)
- Nuxt auto-imports (`ref`, `computed`, `onMounted`) require either Vitest's Nuxt environment or explicit imports in test files
- For full Nuxt environment support: `npm i -D @nuxt/test-utils` and use `defineVitestConfig` from `@nuxt/test-utils/config`
