"""Notification router handling notification list/read/clear endpoints.

The GET /api/notifications endpoint integrates with Unit 2's reminder_checker
to detect newly due/overdue todos on each poll and persist them as
notifications before returning the list.
"""

import os

from fastapi import APIRouter, Depends, Response

from dependencies import get_current_user
from models import (
    MarkAllReadResponse,
    Notification,
    NotificationsListResponse,
    User,
)
from routers.todos import todo_store
from services.notification_service import NotificationService
from services.reminder_checker import check_user
from store import JSONStore

# Initialize notification store and service
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
notification_store = JSONStore(os.path.join(DATA_DIR, "notifications.json"))
notification_service = NotificationService(notification_store)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=NotificationsListResponse)
async def list_notifications(
    current_user: User = Depends(get_current_user),
) -> NotificationsListResponse:
    """List notifications for the authenticated user.

    On each call, integrates with Unit 2's reminder_checker to detect
    newly due reminders or overdue todos and persists them as notifications
    before returning the list. Notifications are ordered DESC by created_at,
    capped at 20. unread_count reflects the FULL unread count (not capped).

    Args:
        current_user: The authenticated user (injected by dependency).

    Returns:
        NotificationsListResponse with notifications list and unread_count.
    """
    user_id = current_user.id

    # 1. Read all todos for this user (raw dicts — reminder_checker expects dicts)
    all_todos = todo_store.read_all()
    user_todos = [t for t in all_todos if t.get("user_id") == user_id]

    # 2. Read all notifications for this user (raw dicts)
    all_notifications = notification_store.read_all()
    user_notifications = [n for n in all_notifications if n.get("user_id") == user_id]

    # 3. Detect new notifications via Unit 2's pure check_user function.
    #    check_user already de-duplicates against existing_notifications, so the
    #    common path is dedup-clean. The defensive exists() call below guards
    #    against race conditions where two concurrent polls could both pass
    #    check_user on the same snapshot before either persists.
    new_notifications = check_user(user_id, user_todos, user_notifications)

    # 4. Persist newly detected notifications
    for todo_id, notification_type, message in new_notifications:
        if not notification_service.exists(user_id, todo_id, notification_type):
            notification_service.create(
                user_id=user_id,
                todo_id=todo_id,
                notification_type=notification_type,
                message=message,
            )

    # 5. Return the full list (sorted DESC, capped at 20) plus full unread_count
    notifications, unread_count = notification_service.list_for_user(user_id)
    return NotificationsListResponse(
        notifications=notifications,
        unread_count=unread_count,
    )


@router.patch("/{notification_id}/read", response_model=Notification)
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
) -> Notification:
    """Mark a single notification as read.

    Verifies ownership and returns 404 if not found or not owned.

    Args:
        notification_id: UUID4 string of the notification to mark.
        current_user: The authenticated user (injected by dependency).

    Returns:
        The updated Notification object.
    """
    return notification_service.mark_as_read(
        user_id=current_user.id,
        notification_id=notification_id,
    )


@router.post("/read-all", response_model=MarkAllReadResponse)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
) -> MarkAllReadResponse:
    """Mark all unread notifications for the user as read.

    Args:
        current_user: The authenticated user (injected by dependency).

    Returns:
        MarkAllReadResponse with marked_count (number of newly marked notifications).
    """
    marked = notification_service.mark_all_as_read(current_user.id)
    return MarkAllReadResponse(marked_count=marked)


@router.delete("", status_code=204)
async def clear_notifications(
    current_user: User = Depends(get_current_user),
) -> Response:
    """Delete all notifications belonging to the user.

    Args:
        current_user: The authenticated user (injected by dependency).

    Returns:
        204 No Content response on success.
    """
    notification_service.clear_all(current_user.id)
    return Response(status_code=204)
