import math
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.schemas import RecalculateRequest, DashboardPayload, ExchangeRateInfo
from app.config import settings
from app.services.etl_service import ETLService
from app.services.trade_service import build_dashboard_payload, scoped_frame
from app.services.auth_service import require_member, require_csrf
from app.services.ai_service import ai_service
from app.services.exchange_rate_service import exchange_rate_service
from app.services.redis_service import redis_service

router = APIRouter(dependencies=[Depends(require_member)])


class PublishedDashboardPayload(DashboardPayload):
    publication: dict | None = None


def validated_rate(value, default):
    rate = default if value is None else value
    if not math.isfinite(rate) or rate <= 0 or rate > 1e9:
        raise HTTPException(422, 'Exchange rate must be finite, positive and at most 1,000,000,000')
    return rate


async def dashboard(db, exchange_rate):
    frame, registry, publication = scoped_frame(db)
    live_info = await exchange_rate_service.fetch_live_rate_async()
    if exchange_rate is None or math.isclose(float(exchange_rate), float(live_info.rate), rel_tol=1e-3):
        rate = validated_rate(None, live_info.rate)
        rate_info = live_info
    else:
        rate = validated_rate(exchange_rate, 4000.0)
        rate_info = ExchangeRateInfo(rate=rate, is_realtime=False, source="User-selected exchange rate", valid_date=live_info.valid_date)

    cache_key = f"agritrade:dashboard:pub:{publication['id']}:rate_{round(rate, 2)}"
    cached = redis_service.get_json(cache_key)
    if cached is not None:
        return PublishedDashboardPayload(**cached)

    _, metrics = ETLService.process_trade_data(frame, exchange_rate=rate, registry=registry)
    scope = {**publication, 'exchange_rate': rate}
    insights = ai_service.generate_chart_meanings_and_strategy(metrics, scope=scope)
    payload = build_dashboard_payload(publication['id'], metrics, rate, insights, exchange_rate_info=rate_info)
    result = PublishedDashboardPayload(**payload.model_dump(), publication=publication)
    redis_service.set_json(cache_key, result.model_dump(), ttl_seconds=settings.REDIS_DASHBOARD_TTL)
    return result


@router.get('/current', response_model=PublishedDashboardPayload)
async def get_current_dashboard(exchange_rate: Optional[float] = Query(None), db: Session = Depends(get_db)):
    return await dashboard(db, exchange_rate)


@router.post('/recalculate', response_model=PublishedDashboardPayload, dependencies=[Depends(require_csrf)])
async def recalculate_analytics(payload: RecalculateRequest, db: Session = Depends(get_db)):
    # Client session_id is deliberately ignored. A past upload is not authorization.
    return await dashboard(db, payload.exchange_rate)
