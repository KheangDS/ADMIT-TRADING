# AgriTrade AI - Standalone Admin Ingestion Portal

This is the dedicated, isolated administrative ingestion portal for **AgriTrade AI**.

## Responsibilities
1. **Confidential Dataset Ingestion**: Securely uploads Cambodian customs Excel (`.xlsx`, `.xls`) and `.csv` files.
2. **Incremental Upsert & Merge**: Merges incoming monthly/annual records with persistent DuckDB storage without overwriting or deleting historic batches.
3. **Database Health & Telemetry**: Displays real-time counts of stored trade records, consolidated revenue, volume, and active reporting periods.
4. **Security**: Communicates directly with protected backend endpoints (`/api/v1/admin/upload`, `/api/v1/admin/status`) using `x-admin-secret-key`.

## How to Run Standalone
```bash
cd admin
npm install
npm run dev
```
By default, the Admin Portal runs at `http://localhost:5174`.

## Integration with External Admin Apps
You can integrate this admin upload functionality into another admin dashboard using:
1. **Direct Component Reuse**: Copy `src/App.vue` into your existing Vue 3 admin app.
2. **Iframe / Micro-Frontend**: Embed `http://<your-admin-domain>:5174` as an internal admin page.
3. **Direct REST API Calls**:
   - `POST /api/v1/admin/upload` (multipart/form-data: `file`, `exchange_rate`, header: `x-admin-secret-key`)
   - `GET /api/v1/admin/status`

