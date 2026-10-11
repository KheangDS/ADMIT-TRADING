# ADMIT administrator portal

Vue 3 + TypeScript, lazy Vue Router pages, Axios cookie-session client. Only backend-provisioned Google administrators can open private pages. All permissions and data validation remain enforced by the backend.

## Run

```sh
npm ci
npm run dev
npm run build
npm test
```

Development runs on `http://localhost:5174`; Vite proxies `/api` to `http://localhost:8000` **only in development**. Configure backend `ADMIN_URL=http://localhost:5174`, exact CORS origins and Google credentials. The OAuth start link uses `return_to=/admin`, a backend sentinel for the configured admin origin. OAuth authorization codes are handled only on the backend.

`VITE_API_BASE_URL` defaults to relative `/api/v1`; see `.env.example`. Production must route `/api` to the backend and fall back to `index.html` for Vue routes. No Vite dev proxy exists in the production build. Cookie Secure should remain enabled in production; opt into backend insecure cookies only for local development. Prefer same-origin HTTPS deployments. Cross-origin configurations must explicitly allow credentials, cookies and trusted origins. Missing OAuth, DB, converter or email setup is not mocked by this portal.

## Workflow

- Bootstrap `/auth/me`; memory-only CSRF with `X-CSRF-Token` for every mutation. Axios `withCredentials: true`; no bearer tokens or authentication local/session storage. Logout/401/403 unmount private pages and discard their state.
- Imports: download bilingual schema template → choose partial/complete and YYYY-MM scope → stage → inspect real errors, exact duplicate count, mapping and change preview → resolve every unknown HS4/HS8/country with English + Khmer using exact backend codes → refresh staged review → explicitly confirm commit. Invalid imports never show an ingestion-success banner. Complete replacement confirms omitted-row removal; stale commits expose 409 and require restaging/review.
- Publication: choose a ready immutable revision and reporting bounds, review configuration and explicitly confirm release. The scope preview is not fabricated calculated analytics.
- Documents: privately upload PDF/PPT/PPTX drafts, edit metadata, explicitly publish/withdraw/delete, fetch authorized originals and PDF blob previews. Missing/pending/failed conversion is shown truthfully. Blob URLs are revoked when previews close or the page unmounts. Reports are not sent to AI.
- Plans: USD (max 2 decimals) / integer KHR, positive calendar-month/year durations. Deactivate rather than delete; payment pricing remains frozen.
- Payments: account Google name/email, uppercase payer, original confirmation/approval/paid timestamps, checkout IP/device/user agent. Human matching only; approval requires real unique bank reference and actual paid-at in Phnom Penh time. Reject with reason. No screenshot, bot or bank integration. List polls every 60 seconds only when visible and no review is open, stopping on unmount.
- Users: reason-required manual grant/revoke; administrator role changes remain CLI-only.
- Audit/outbox: display real safe backend diagnostics and explicitly retry failed jobs. Retry acceptance is not receipt/email delivery success.

All collection endpoints consume the contract's plain arrays, not invented `{items: ...}` wrappers. Times display `Asia/Phnom_Penh` and datetime-local administrative fields explicitly interpret UTC+07:00, independent of browser timezone. Form controls have labels, notices have live roles, destructive actions use keyboard-accessible native modal dialogs.

Tests cover API bootstrap/CSRF, unauthorized session clearing, OAuth routing, task error handling, month/time validation and timer cleanup using mocked adapters (not live Google, bank or email verification).
