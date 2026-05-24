"""Notification service handling notification CRUD operations scoped to authenticated users."""

import uuid
from datetime import datetime, timezone

from exceptions import NotFoundError
from models import Notification, NotificationType
from store import JSONStore


class NotificationService:
    """Handles CRUD operations on notifications scoped to the authenticated user."""

    def __init__(self, notification_store: JSONStore):
        """Initialize with notification store.

        Args:
            notification_store: JSONStore instance for notification persistence.
        """
        self.notification_store = notification_store

    def create(
        self,
        user_id: str,
        todo_id: str,
        notification_type: str,
        message: str,
    ) -> Notification:
        """Create a new notification.

        Generates a UUID4 id, sets is_read=False, stamps created_at, and persists.
        Does NOT perform deduplication — callers are responsible for checking
        via `exists()` before creating, or relying on `reminder_checker.check_user()`'s
        built-in deduplication.

        Args:
            user_id: UUID4 string of the notification owner.
            todo_id: UUID4 string of the related todo.
            notification_type: "reminder" or "overdue".
            message: Human-readable notification message.

        Returns:
            The created Notification object.
        """
        # Normalize type to its string value for consistent storage
        type_value = (
            notification_type.value
            if isinstance(notification_type, NotificationType)
            else str(notification_type)
        )

        record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "todo_id": todo_id,
            "type": type_value,
            "message": message,
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self.notification_store.add(record)

        return Notification(**record)

    def exists(
        self,
        user_id: str,
        todo_id: str,
        notification_type: str,
    ) -> bool:
        """Check if a notification already exists for deduplication.

        Args:
            user_id: UUID4 string of the notification owner.
            todo_id: UUID4 string of the related todo.
            notification_type: "reminder" or "overdue".

        Returns:
            True if a notification with this (user_id, todo_id, type) exists.
        """
        type_value = (
            notification_type.value
            if isinstance(notification_type, NotificationType)
            else str(notification_type)
        )

        records = self.notification_store.read_all()
        for record in records:
            if (
                record.get("user_id") == user_id
                and record.get("todo_id") == todo_id
                and record.get("type") == type_value
            ):
                return True
        return False

    def list_for_user(
        self,
        user_id: str,
        limit: int = 20,
    ) -> tuple[list[Notification], int]:
        """List notifications for a user, ordered DESC by created_at, plus full unread count.

        Args:
            user_id: UUID4 string of the notification owner.
            limit: Maximum number of notifications to return (default 20).

        Returns:
            A tuple of (notifications, unread_count) where:
            - notifications: list of Notification objects ordered DESC by created_at, capped at `limit`.
            - unread_count: total count of unread notifications for this user (NOT capped by limit).
        """
        records = self.notification_store.read_all()
        user_records = [r for r in records if r.get("user_id") == user_id]

        # Compute unread_count over the FULL set (not the capped list)
        unread_count = sum(1 for r in user_records if not r.get("is_read", False))

        # Sort DESC by created_at and cap at limit
        user_records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        capped = user_records[:limit]

        notifications = [Notification(**r) for r in capped]
        return notifications, unread_count

    def mark_as_read(self, user_id: str, notification_id: str) -> Notification:
        """Mark a single notification as read.

        Verifies ownership (returns 404 if not found or not owned).

        Args:
            user_id: UUID4 string of the notification owner.
            notification_id: UUID4 string of the notification to mark.

        Returns:
            The updated Notification object.

        Raises:
            NotFoundError: If notification is not found or not owned by user.
        """
        record = self.notification_store.find_by_id(notification_id)

        if not record or record.get("user_id") != user_id:
            raise NotFoundError("Notification not found")

        updated = self.notification_store.update(notification_id, {"is_read": True})

        if not updated:
            raise NotFoundError("Notification not found")

        return Notification(**updated)

    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all unread notifications for the user as read.

        Args:
            user_id: UUID4 string of the notification owner.

        Returns:
            The count of notifications that were newly marked as read
            (i.e., were previously unread).
        """
        records = self.notification_store.read_all()
        marked = 0

        for record in records:
            if record.get("user_id") == user_id and not record.get("is_read", False):
                record["is_read"] = True
                marked += 1

        if marked > 0:
            self.notification_store.write_all(records)

        return marked

    def clear_all(self, user_id: str) -> None:
        """Delete all notifications belonging to the user.

        Args:
            user_id: UUID4 string of the notification owner.
        """
        records = self.notification_store.read_all()
        remaining = [r for r in records if r.get("user_id") != user_id]

        # Only write if there's actually a change to persist
        if len(remaining) != len(records):
            self.notification_store.write_all(remaining)
