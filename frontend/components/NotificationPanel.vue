<template>
  <div
    class="absolute right-0 mt-2 w-80 sm:w-96 bg-white dark:bg-secondary-800 rounded-lg shadow-xl border border-secondary-200 dark:border-secondary-700 z-50 overflow-hidden"
    role="dialog"
    aria-label="Notifications"
    @click.stop
  >
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-secondary-200 dark:border-secondary-700">
      <h3 class="text-sm font-semibold text-secondary-900 dark:text-white">
        Notifications
        <span
          v-if="unreadCount > 0"
          class="ml-1 text-xs font-normal text-secondary-500 dark:text-secondary-400"
        >
          ({{ unreadCount }} unread)
        </span>
      </h3>
      <div class="flex items-center gap-1">
        <button
          type="button"
          class="text-xs px-2 py-1 rounded text-primary-600 hover:bg-primary-50 dark:text-primary-400 dark:hover:bg-primary-900/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-primary-500"
          :disabled="unreadCount === 0"
          data-testid="notification-panel-mark-all-read"
          aria-label="Mark all notifications as read"
          @click="$emit('mark-all-read')"
        >
          Mark all read
        </button>
        <button
          type="button"
          class="text-xs px-2 py-1 rounded text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-red-500"
          :disabled="notifications.length === 0"
          data-testid="notification-panel-clear-all"
          aria-label="Clear all notifications"
          @click="$emit('clear-all')"
        >
          Clear all
        </button>
      </div>
    </div>

    <!-- Body -->
    <div class="max-h-96 overflow-y-auto">
      <!-- Loading state -->
      <div
        v-if="loading && notifications.length === 0"
        class="px-4 py-8 text-center text-sm text-secondary-500 dark:text-secondary-400"
        data-testid="notification-panel-loading"
      >
        <svg
          class="animate-spin h-5 w-5 mx-auto mb-2 text-primary-600 dark:text-primary-400"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Loading...
      </div>

      <!-- Empty state -->
      <div
        v-else-if="notifications.length === 0"
        class="px-4 py-10 text-center"
        data-testid="notification-panel-empty"
      >
        <svg
          class="w-10 h-10 mx-auto text-secondary-300 dark:text-secondary-600 mb-2"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        <p class="text-sm text-secondary-500 dark:text-secondary-400">No notifications yet</p>
      </div>

      <!-- List -->
      <ul v-else class="divide-y divide-secondary-100 dark:divide-secondary-700" role="list">
        <li
          v-for="notification in notifications"
          :key="notification.id"
          :class="[
            'px-4 py-3 transition-colors duration-150',
            notification.is_read
              ? 'bg-white dark:bg-secondary-800'
              : 'bg-primary-50 dark:bg-primary-900/10 hover:bg-primary-100 dark:hover:bg-primary-900/20 cursor-pointer',
          ]"
          :data-testid="`notification-item-${notification.id}`"
          :tabindex="notification.is_read ? -1 : 0"
          :role="notification.is_read ? undefined : 'button'"
          :aria-label="notification.is_read ? undefined : `Mark notification as read: ${notification.message}`"
          @click="handleItemClick(notification)"
          @keydown.enter.prevent="handleItemClick(notification)"
          @keydown.space.prevent="handleItemClick(notification)"
        >
          <div class="flex items-start gap-3">
            <!-- Type icon -->
            <div
              :class="[
                'flex-shrink-0 mt-0.5 w-8 h-8 rounded-full flex items-center justify-center',
                notification.type === 'reminder'
                  ? 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400'
                  : 'bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400',
              ]"
              aria-hidden="true"
            >
              <!-- Reminder: clock icon -->
              <svg
                v-if="notification.type === 'reminder'"
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <!-- Overdue: alert icon -->
              <svg
                v-else
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <p
                :class="[
                  'text-sm',
                  notification.is_read
                    ? 'text-secondary-700 dark:text-secondary-300'
                    : 'text-secondary-900 dark:text-white font-medium',
                ]"
              >
                {{ notification.message }}
              </p>
              <p class="mt-0.5 text-xs text-secondary-500 dark:text-secondary-400">
                {{ formatRelativeTime(notification.created_at) }}
              </p>
            </div>

            <!-- Unread dot -->
            <div
              v-if="!notification.is_read"
              class="flex-shrink-0 mt-2 w-2 h-2 rounded-full bg-primary-600 dark:bg-primary-400"
              aria-hidden="true"
            ></div>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Notification } from '~/types'

interface Props {
  notifications: Notification[]
  unreadCount: number
  loading: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'mark-read', id: string): void
  (e: 'mark-all-read'): void
  (e: 'clear-all'): void
  (e: 'close'): void
}>()

function handleItemClick(notification: Notification) {
  if (!notification.is_read) {
    emit('mark-read', notification.id)
  }
}

function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString)
  if (isNaN(date.getTime())) return ''

  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffSec < 60) return 'just now'
  if (diffMin < 60) return `${diffMin} minute${diffMin === 1 ? '' : 's'} ago`
  if (diffHour < 24) return `${diffHour} hour${diffHour === 1 ? '' : 's'} ago`
  if (diffDay < 7) return `${diffDay} day${diffDay === 1 ? '' : 's'} ago`

  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>
