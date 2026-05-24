import { notificationsApi } from '~/utils/api'
import type { Notification } from '~/types'

const POLL_INTERVAL_MS = 30_000

// Module-level singleton state (same pattern as useToast)
const notifications = ref<Notification[]>([])
const unreadCount = ref<number>(0)
const loading = ref<boolean>(false)
const error = ref<string | null>(null)

let pollTimer: ReturnType<typeof setInterval> | null = null

function extractErrorMessage(err: any): string {
  const statusCode = err?.response?.status || err?.statusCode || err?.status
  const data = err?.response?._data || err?.data

  if (statusCode === 401) {
    return data?.detail || 'Authentication required'
  }

  if (statusCode === 404) {
    return data?.detail || 'Notification not found'
  }

  if (err?.message === 'Request timed out. Please try again.') {
    return err.message
  }

  if (err?.message) {
    return err.message
  }

  return 'Something went wrong. Please try again.'
}

function recomputeUnreadCount() {
  unreadCount.value = notifications.value.filter((n) => !n.is_read).length
}

export function useNotifications() {
  function clearError() {
    error.value = null
  }

  async function fetchNotifications(): Promise<void> {
    clearError()
    loading.value = true
    try {
      const response = await notificationsApi.list()
      notifications.value = response.notifications
      unreadCount.value = response.unread_count
    } catch (err: any) {
      // Don't surface 401 as an error during background polling — user may be logging out
      const statusCode = err?.response?.status || err?.statusCode || err?.status
      if (statusCode !== 401) {
        error.value = extractErrorMessage(err)
      }
    } finally {
      loading.value = false
    }
  }

  async function markAsRead(id: string): Promise<void> {
    clearError()

    // Optimistic update
    const index = notifications.value.findIndex((n) => n.id === id)
    if (index === -1) return
    if (notifications.value[index].is_read) return // already read, nothing to do

    const original = { ...notifications.value[index] }
    notifications.value[index] = { ...original, is_read: true }
    recomputeUnreadCount()

    try {
      const updated = await notificationsApi.markAsRead(id)
      const currentIndex = notifications.value.findIndex((n) => n.id === id)
      if (currentIndex !== -1) {
        notifications.value[currentIndex] = updated
        recomputeUnreadCount()
      }
    } catch (err: any) {
      // Rollback
      const rollbackIndex = notifications.value.findIndex((n) => n.id === id)
      if (rollbackIndex !== -1) {
        notifications.value[rollbackIndex] = original
      } else {
        notifications.value.splice(index, 0, original)
      }
      recomputeUnreadCount()
      error.value = extractErrorMessage(err)
    }
  }

  async function markAllAsRead(): Promise<void> {
    clearError()

    if (unreadCount.value === 0) return

    // Optimistic update — snapshot for rollback
    const snapshot = notifications.value.map((n) => ({ ...n }))
    notifications.value = notifications.value.map((n) =>
      n.is_read ? n : { ...n, is_read: true }
    )
    unreadCount.value = 0

    try {
      await notificationsApi.markAllAsRead()
    } catch (err: any) {
      // Rollback
      notifications.value = snapshot
      recomputeUnreadCount()
      error.value = extractErrorMessage(err)
    }
  }

  async function clearAll(): Promise<void> {
    clearError()

    if (notifications.value.length === 0) return

    // Optimistic update — snapshot for rollback
    const snapshot = notifications.value.map((n) => ({ ...n }))
    notifications.value = []
    unreadCount.value = 0

    try {
      await notificationsApi.clearAll()
    } catch (err: any) {
      // Rollback
      notifications.value = snapshot
      recomputeUnreadCount()
      error.value = extractErrorMessage(err)
    }
  }

  function startPolling(): void {
    // Idempotent: if already polling, do nothing
    if (pollTimer !== null) return

    // Initial fetch immediately
    void fetchNotifications()

    pollTimer = setInterval(() => {
      void fetchNotifications()
    }, POLL_INTERVAL_MS)
  }

  function stopPolling(): void {
    if (pollTimer !== null) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  return {
    // State
    notifications,
    unreadCount,
    loading,
    error,

    // Actions
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    clearAll,
    startPolling,
    stopPolling,
    clearError,
  }
}
