<template>
  <div ref="rootRef" class="relative">
    <button
      type="button"
      class="relative p-2 rounded-md text-secondary-600 hover:text-primary-600 hover:bg-secondary-100 dark:text-secondary-300 dark:hover:text-primary-400 dark:hover:bg-secondary-700 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-primary-500"
      :aria-label="ariaLabel"
      aria-haspopup="dialog"
      :aria-expanded="isOpen"
      data-testid="notification-bell-button"
      @click="togglePanel"
    >
      <svg
        class="w-5 h-5"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>

      <!-- Unread badge -->
      <span
        v-if="unreadCount > 0"
        class="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 rounded-full bg-red-600 text-white text-[10px] font-semibold flex items-center justify-center leading-none"
        :aria-label="`${unreadCount} unread notifications`"
        data-testid="notification-bell-badge"
      >
        {{ badgeText }}
      </span>
    </button>

    <!-- Panel -->
    <Transition
      enter-active-class="transition duration-150 ease-out"
      leave-active-class="transition duration-100 ease-in"
      enter-from-class="opacity-0 -translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-1"
    >
      <NotificationPanel
        v-if="isOpen"
        :notifications="notifications"
        :unread-count="unreadCount"
        :loading="loading"
        @mark-read="onMarkRead"
        @mark-all-read="onMarkAllRead"
        @clear-all="onClearAll"
        @close="closePanel"
      />
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { useNotifications } from '~/composables/useNotifications'

const {
  notifications,
  unreadCount,
  loading,
  fetchNotifications,
  markAsRead,
  markAllAsRead,
  clearAll,
  startPolling,
  stopPolling,
} = useNotifications()

const isOpen = ref(false)
const rootRef = ref<HTMLElement | null>(null)

const badgeText = computed(() => (unreadCount.value > 9 ? '9+' : String(unreadCount.value)))

const ariaLabel = computed(() =>
  unreadCount.value > 0
    ? `Notifications, ${unreadCount.value} unread`
    : 'Notifications'
)

function togglePanel() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    // Refresh on open so the user sees the latest immediately
    void fetchNotifications()
  }
}

function closePanel() {
  isOpen.value = false
}

function onMarkRead(id: string) {
  void markAsRead(id)
}

function onMarkAllRead() {
  void markAllAsRead()
}

function onClearAll() {
  void clearAll()
}

function handleDocumentClick(event: MouseEvent) {
  if (!isOpen.value) return
  const target = event.target as Node | null
  if (rootRef.value && target && !rootRef.value.contains(target)) {
    closePanel()
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && isOpen.value) {
    closePanel()
  }
}

onMounted(() => {
  startPolling()
  if (typeof document !== 'undefined') {
    document.addEventListener('click', handleDocumentClick)
    document.addEventListener('keydown', handleKeydown)
  }
})

onBeforeUnmount(() => {
  stopPolling()
  if (typeof document !== 'undefined') {
    document.removeEventListener('click', handleDocumentClick)
    document.removeEventListener('keydown', handleKeydown)
  }
})
</script>
