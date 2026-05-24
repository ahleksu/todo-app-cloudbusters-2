# Build Instructions — Reminders & Notifications (Units 1, 2, 4)

## Prerequisites
- **Python**: 3.11+
- **Node.js**: 18+ (for frontend)
- **pip**: Latest version
- **Working Directories**: `backend/` for the API, `frontend/` for the Nuxt app

## Backend Build

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

No new dependencies were added for Units 1, 2, or 4. The existing `requirements.txt` covers all needs (Pydantic for models, FastAPI for routing).

### 2. Verify Python Syntax
```bash
cd backend
python -m py_compile models.py services/todo_service.py services/reminder_checker.py services/notification_service.py routers/notifications.py main.py && echo OK
```

### 3. Verify Imports
```bash
cd backend
python -c "from models import Todo, TodoCreate, TodoUpdate, Notification, NotificationsListResponse, MarkAllReadResponse, NotificationType; print('Models import OK')"
python -c "from services.reminder_checker import check_user; print('ReminderChecker import OK')"
python -c "from services.todo_service import TodoService; print('TodoService import OK')"
python -c "from services.notification_service import NotificationService; print('NotificationService import OK')"
python -c "from routers.notifications import router; print('Notifications router import OK')"
```

### 4. Verify Data Files Exist
```bash
ls -la backend/data/todos.json backend/data/users.json backend/data/notifications.json
```

If `notifications.json` does not exist, create it as an empty array:
```bash
echo "[]" > backend/data/notifications.json
```

### 5. Start the Backend Server
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 6. Verify Build Success
- **Expected Output**: Server starts on `http://localhost:8000`
- **Health Check**: `curl http://localhost:8000/` returns `{"status":"ok","message":"Todo App API"}`
- **Routes registered**: at startup the FastAPI logs should show routes for `/api/auth/*`, `/api/todos/*`, and `/api/notifications/*`
- **No import errors** in server startup logs

## Frontend Build (Unit 4)

### 1. Install Dependencies
```bash
cd frontend
npm install
```

No new dependencies were added for Unit 4. Existing Nuxt 3 / Vue 3 stack covers everything.

### 2. Type-check the project
```bash
cd frontend
npx nuxi typecheck
```

### 3. Start the Dev Server
```bash
cd frontend
npm run dev
```

Default URL: `http://localhost:3000`

## Troubleshooting

### Import Error: `models` module
- **Cause**: Running from wrong directory
- **Solution**: Ensure you're in the `backend/` directory when running

### `404 Not Found` on `/api/notifications`
- **Cause**: Notifications router not registered
- **Solution**: Verify `backend/main.py` imports and includes `notifications_router`

### `IOError: Failed to read store file: backend/data/notifications.json`
- **Cause**: Data directory permissions issue (rare)
- **Solution**: Ensure the process has write permissions to `backend/data/`. The `JSONStore` will auto-create `notifications.json` on first read if missing, but the directory must be writable.

### Pydantic Validation Error on Startup
- **Cause**: Model field type mismatch
- **Solution**: Verify `reminder_at` field types match (`datetime | None` in Todo, `str | None` in TodoCreate/TodoUpdate). Verify `Notification.type` is `NotificationType` enum.
