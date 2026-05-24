# Build Instructions — Unit 3: Notification Bell UI

## Prerequisites
- **Node.js**: 18.x or 20.x
- **npm**: 9+ (or pnpm/yarn equivalent)
- **Working Directory**: `frontend/`
- **Backend**: Unit 1 must be running on `http://localhost:8000` for the bell to receive real data (otherwise it polls and silently shows the empty state).

## Build Steps

### 1. Install Dependencies
```bash
cd frontend
npm install
```

No new dependencies were added for Unit 3. The existing `package.json` covers all needs (Vue 3, Nuxt 3, TypeScript).

### 2. Run TypeScript Type Check
Nuxt's `prepare` step generates `.nuxt/tsconfig.json`; the editor / IDE will surface any TS errors. To run an explicit type check:

```bash
cd frontend
npx nuxi prepare
npx vue-tsc --noEmit
```

Note: `vue-tsc` is not currently a dev dependency. If type checking is desired in CI, add it: `npm i -D vue-tsc`.

### 3. Production Build
```bash
cd frontend
npm run build
```

Expected output: Nuxt completes the build with no errors. Build artifacts are written to `.output/`.

### 4. Dev Server (Manual Verification)
```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`, log in, and confirm the bell icon appears in the dashboard navbar between the dark-mode toggle and the Logout button.

## Files Touched in This Build
- Created: `frontend/composables/useNotifications.ts`
- Created: `frontend/components/NotificationPanel.vue`
- Created: `frontend/components/NotificationBell.vue`
- Modified: `frontend/types/index.ts`
- Modified: `frontend/utils/api.ts`
- Modified: `frontend/pages/dashboard.vue`

## Troubleshooting

### Bell shows but badge never updates
- **Cause**: Backend `/api/notifications` endpoint not running (Unit 1 not deployed) or auth cookie not set
- **Solution**: Start backend (`uvicorn main:app --reload --port 8000`); log in via the frontend so the `token` cookie is set; verify `GET /api/notifications` returns 200 in browser network tab

### Console error: "Failed to fetch" every 30 seconds
- **Cause**: Backend not reachable at `http://localhost:8000`
- **Solution**: Confirm backend is running and `BASE_URL` in `frontend/utils/api.ts` matches

### Polling continues after logout
- **Cause**: `NotificationBell` component still mounted (e.g., navigated away from dashboard but kept alive)
- **Solution**: Verify `onBeforeUnmount` is firing; the bell should only be mounted on the dashboard page

### "9+" badge instead of expected number
- **Behaviour by design**: Counts above 9 are capped to "9+" for visual cleanliness. The full count is still in the `aria-label`.
