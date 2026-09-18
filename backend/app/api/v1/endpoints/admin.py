from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, status
from app.config import settings
from app.services.etl_service import ETLService
from app.services.duckdb_service import duckdb_service
from app.services.ai_service import ai_service
from app.models.schemas import AdminUploadResponse, AdminStatusResponse, DashboardPayload
from app.api.v1.endpoints.upload import build_dashboard_payload

from app.services.exchange_rate_service import exchange_rate_service
from app.services.redis_service import redis_service

router = APIRouter()

def verify_admin_key(x_admin_secret_key: Optional[str] = Header(None)):
    """Verifies optional admin secret key for extra security."""
    if settings.ADMIN_SECRET_KEY and x_admin_secret_key:
        if x_admin_secret_key != settings.ADMIN_SECRET_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Admin Secret Key. Access denied."
            )

@router.get("/status", response_model=AdminStatusResponse)
async def get_admin_db_status():
    """Returns persistent DuckDB storage statistics and live exchange rate info with Redis caching."""
    # Check Redis Cache
    cached_status = redis_service.get_cached_admin_status()
    if cached_status and cached_status.get('upload_history'):
        return AdminStatusResponse(**cached_status)

    rate_info = await exchange_rate_service.fetch_live_rate_async()
    df_master = duckdb_service.get_master_dataframe()
    upload_history = duckdb_service.get_upload_history()
    
    if df_master.empty:
        status_res = AdminStatusResponse(
            total_records=0,
            total_export_val_usd=0.0,
            total_weight_tonnes=0.0,
            reporting_period="No Data Ingested",
            hs4_chapters_count=0,
            last_updated="N/A",
            exchange_rate_info=rate_info,
            upload_history=upload_history
        )
        redis_service.set_cached_admin_status(status_res.model_dump())
        return status_res
    
    _, metrics = ETLService.process_trade_data(df_master, exchange_rate=rate_info.rate)
    
    b_date = metrics.get('begin_date')
    e_date = metrics.get('end_date')
    period_str = f"{b_date} – {e_date}" if (b_date and e_date) else "All Available"
    
    status_res = AdminStatusResponse(
        total_records=len(df_master),
        total_export_val_usd=round(metrics['total_val_usd'], 2),
        total_weight_tonnes=round(metrics['total_weight_ton'], 2),
        reporting_period=period_str,
        hs4_chapters_count=len(metrics.get('hs4_summary', [])),
        last_updated=str(df_master['updated_at'].max()) if 'updated_at' in df_master.columns else "Active",
        exchange_rate_info=rate_info,
        upload_history=upload_history
    )
    redis_service.set_cached_admin_status(status_res.model_dump())
    return status_res

@router.get("/exchange-rate")
async def get_admin_exchange_rate():
    """Returns real-time exchange rate details directly from MEF API."""
    return await exchange_rate_service.fetch_live_rate_async(force_refresh=True)

@router.get("/cache-status")
async def get_cache_diagnostics():
    """Returns real-time Redis cache diagnostics."""
    return redis_service.get_status()

@router.post("/upload", response_model=AdminUploadResponse)
async def admin_upload_dataset(
    file: UploadFile = File(...),
    exchange_rate: Optional[float] = Form(None),
    x_admin_secret_key: Optional[str] = Header(None)
):
    """
    Dedicated Admin Ingestion Endpoint:
    1. Ingests Excel or CSV file.
    2. Validates customs trade schema.
    3. Performs 5-stage ETL cleaning using real-time MEF exchange rate.
    4. Incrementally upserts records into persistent DuckDB without overwriting historical batches.
    5. Recomputes global metrics & AI strategic insights.
    """
    verify_admin_key(x_admin_secret_key)
    
    rate_info = await exchange_rate_service.fetch_live_rate_async()
    rate_val = exchange_rate if (exchange_rate and exchange_rate > 0) else rate_info.rate
    
    contents = await file.read()
    
    # 1. Parse File
    try:
        df_raw = ETLService.inspect_and_load_file(contents, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse Excel/CSV file: {str(e)}")
        
    # 2. Validate Trade Schema
    is_valid, msg, col_map = ETLService.validate_trade_schema(df_raw)
    if not is_valid:
        return AdminUploadResponse(
            success=False,
            message=msg,
            rows_inserted=0,
            rows_updated=0,
            total_records=duckdb_service.get_records_count(),
            reporting_period="N/A",
            exchange_rate_info=rate_info,
            dashboard_payload=None
        )
        
    # 3. Clean and normalize incoming batch
    df_clean, _ = ETLService.process_trade_data(df_raw, col_map, exchange_rate=rate_val)
    
    # 4. Incremental Upsert into Persistent DuckDB
    try:
        rows_inserted, rows_updated, total_records = duckdb_service.upsert_dataframe(df_clean)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database upsert failed: {str(e)}")
        
    # 5. Re-aggregate full master dataset
    try:
        df_master = duckdb_service.get_master_dataframe()
        _, master_metrics = ETLService.process_trade_data(df_master, exchange_rate=rate_val)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Master aggregation failed: {str(e)}")
    
    # 6. Generate AI insights for updated dataset
    ai_insights = ai_service.generate_chart_meanings_and_strategy(master_metrics)
    
    dashboard_payload = build_dashboard_payload("master", master_metrics, rate_val, ai_insights, exchange_rate_info=rate_info)
    
    # Invalidate stale Redis caches and pre-populate fresh dataset
    redis_service.invalidate_all_trade_caches()
    redis_service.set_cached_dashboard(rate_val, dashboard_payload.model_dump())
    
    b_m = master_metrics.get('begin_date')
    e_m = master_metrics.get('end_date')
    period_str = f"{b_m} – {e_m}" if (b_m and e_m) else "All Available"
    
    # Record in persistent upload history log
    duckdb_service.record_upload(
        filename=file.filename,
        rows_inserted=rows_inserted,
        rows_updated=rows_updated,
        total_records=total_records,
        period_range=period_str
    )
    
    return AdminUploadResponse(
        success=True,
        message=f"Dataset successfully ingested! Added {rows_inserted} new records, updated {rows_updated} existing records. Database now holds {total_records} total trade records.",
        rows_inserted=rows_inserted,
        rows_updated=rows_updated,
        total_records=total_records,
        reporting_period=period_str,
        exchange_rate_info=rate_info,
        dashboard_payload=dashboard_payload,
        upload_history=duckdb_service.get_upload_history()
    )

