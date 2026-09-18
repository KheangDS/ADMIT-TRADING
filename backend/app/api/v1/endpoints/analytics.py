from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import RecalculateRequest, DashboardPayload
from app.api.v1.endpoints.upload import SESSION_STORE, build_dashboard_payload
from app.services.etl_service import ETLService
from app.services.duckdb_service import duckdb_service
from app.services.ai_service import ai_service

from app.services.exchange_rate_service import exchange_rate_service
from app.services.redis_service import redis_service

router = APIRouter()

@router.get("/current", response_model=DashboardPayload)
async def get_current_dashboard(exchange_rate: Optional[float] = Query(None, description="Current KHR to USD rate (optional, defaults to real-time MEF rate)")):
    """
    Public Read-Only Endpoint:
    Returns the latest consolidated trade analytics directly from the persistent database
    or instant Redis cache using real-time MEF exchange rates.
    """
    rate_info = await exchange_rate_service.fetch_live_rate_async()
    rate_val = exchange_rate if (exchange_rate and exchange_rate > 0) else rate_info.rate

    # 1. Check Redis Cache First
    cached_payload = redis_service.get_cached_dashboard(rate_val)
    if cached_payload:
        return DashboardPayload(**cached_payload)

    # 2. Cache Miss - Query Persistent Database
    df_master = duckdb_service.get_master_dataframe()
    if df_master.empty:
        return DashboardPayload(
            session_id="master",
            is_valid_trade_data=False,
            validation_message="No trade dataset has been uploaded to the database yet. Please upload via the Admin Portal.",
            exchange_rate=rate_val,
            exchange_rate_info=rate_info
        )
        
    _, master_metrics = ETLService.process_trade_data(df_master, exchange_rate=rate_val)
    ai_insights = ai_service.generate_chart_meanings_and_strategy(master_metrics)
    
    dashboard_payload = build_dashboard_payload("master", master_metrics, rate_val, ai_insights, exchange_rate_info=rate_info)
    
    # 3. Store in Redis Cache for subsequent requests
    redis_service.set_cached_dashboard(rate_val, dashboard_payload.model_dump())
    
    return dashboard_payload

@router.post("/recalculate", response_model=DashboardPayload)
async def recalculate_analytics(payload: RecalculateRequest):
    session_id = payload.session_id or "master"
    rate_info = await exchange_rate_service.fetch_live_rate_async()
    rate_val = payload.exchange_rate if (payload.exchange_rate and payload.exchange_rate > 0) else rate_info.rate
    
    if session_id == "master" or session_id not in SESSION_STORE:
        # Check Redis Cache First
        cached_payload = redis_service.get_cached_dashboard(rate_val)
        if cached_payload:
            return DashboardPayload(**cached_payload)
            
        # Pull from persistent database
        df_master = duckdb_service.get_master_dataframe()
        if df_master.empty:
            raise HTTPException(status_code=404, detail="No trade data found in persistent database.")
        _, metrics = ETLService.process_trade_data(df_master, exchange_rate=rate_val)
        ai_insights = ai_service.generate_chart_meanings_and_strategy(metrics)
        dash_payload = build_dashboard_payload("master", metrics, rate_val, ai_insights, exchange_rate_info=rate_info)
        redis_service.set_cached_dashboard(rate_val, dash_payload.model_dump())
        return dash_payload
        
    session_data = SESSION_STORE[session_id]
    df_clean = session_data['df_clean']
    col_map = session_data.get('col_map')
    
    # Recalculate metrics with exchange rate
    _, metrics = ETLService.process_trade_data(df_clean, col_map, exchange_rate=rate_val)
    ai_insights = ai_service.generate_chart_meanings_and_strategy(metrics)
    
    # Update stored metrics
    SESSION_STORE[session_id]['metrics'] = metrics
    
    return build_dashboard_payload(session_id, metrics, rate_val, ai_insights, exchange_rate_info=rate_info)

