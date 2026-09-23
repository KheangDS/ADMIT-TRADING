import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import pandas as pd

from app.models.schemas import (
    DashboardPayload,
    KpiMetric,
    AiMeaning,
    ChartConfig,
    Hs4CategorySummary,
    Hs8CommoditySummary,
    MarketShareItem,
    CommodityListItem,
    ExchangeRateInfo
)
from app.services.etl_service import ETLService
from app.services.duckdb_service import duckdb_service
from app.services.ai_service import ai_service
from app.services.exchange_rate_service import exchange_rate_service
from app.services.redis_service import redis_service
from app.services.hs_product_service import (
    get_hs8_product_info,
    get_country_info,
    get_hs4_official_name,
    clean_hs_code
)

router = APIRouter()

# In-Memory Session Store for interactive sessions
SESSION_STORE: Dict[str, Dict[str, Any]] = {}

def build_dashboard_payload(
    session_id: str,
    metrics: Dict[str, Any],
    exchange_rate: float,
    ai_insights: Dict[str, Any],
    exchange_rate_info: Optional[ExchangeRateInfo] = None
) -> DashboardPayload:
    """Standardizes metrics and generated AI insights into the API Response Payload."""
    total_val_usd = metrics['total_val_usd']
    total_val_khr = metrics['total_val_khr']
    total_weight_ton = metrics['total_weight_ton']
    active_countries_count = len(metrics.get('available_countries', []))
    total_hs8_count = len(metrics.get('commodity_list', []))
    
    # 1. Summary KPIs
    summary_kpis = [
        KpiMetric(
            label="Revenue (USD)",
            value=f"${total_val_usd/1e6:,.2f}M USD",
            numeric_val=total_val_usd,
            unit="USD",
            description="Total agricultural export revenue"
        ),
        KpiMetric(
            label="Revenue (KHR)",
            value=f"{total_val_khr/1e9:,.2f}B KHR",
            numeric_val=total_val_khr,
            unit="KHR",
            description="Raw trade currency total"
        ),
        KpiMetric(
            label="Export Volume",
            value=f"{total_weight_ton:,.2f} Tonnes",
            numeric_val=total_weight_ton,
            unit="Tonnes",
            description="Total agricultural export weight"
        ),
        KpiMetric(
            label="Destination Markets",
            value=f"{active_countries_count} Countries",
            numeric_val=float(active_countries_count),
            unit="Markets",
            description="Active international trading partners"
        ),
        KpiMetric(
            label="Total Commodities",
            value=f"{total_hs8_count} Commodities",
            numeric_val=float(total_hs8_count),
            unit="Commodities",
            description="Active 8-digit tariff line products"
        )
    ]
    
    # 2. HS8 Commodities (Primary Level)
    hs8_list = []
    for item in metrics.get('hs8_commodities', metrics.get('hs8_summary', [])):
        code = clean_hs_code(item.get('hs8_code', ''), 8)
        hs4 = clean_hs_code(item.get('hs4_code', ''), 4)
        info = get_hs8_product_info(code) if code else {}
        name_en = item.get('name_en') or item.get('product_name') or info.get('name_en') or f"HS {code}"
        name_km = item.get('name_km') or item.get('name_kh') or info.get('name_kh') or name_en
        cat_en = item.get('category_en') or info.get('category_en') or 'Other Agricultural'
        cat_km = item.get('category_km') or item.get('category_kh') or info.get('category_kh') or 'កសិផលផ្សេងៗ'
        val_usd = float(item.get('val_usd', 0.0) or 0.0)
        val_khr = float(item.get('val_khr', val_usd * exchange_rate) or 0.0)
        weight_ton = float(item.get('weight_ton', 0.0) or 0.0)
        weight_kg = float(item.get('weight_kg', 0.0) or (weight_ton * 1000.0))
        unit_price = item.get('unit_price_usd_per_kg')
        if unit_price is None:
            unit_price = (val_usd / weight_kg) if weight_kg > 0 else 0.0

        hs8_list.append(
            Hs8CommoditySummary(
                hs8_code=code,
                hs4_code=hs4,
                name_en=name_en,
                name_km=name_km,
                category_en=cat_en,
                category_km=cat_km,
                weight_tonnes=round(weight_ton, 2),
                weight_kg=round(weight_kg, 2),
                val_usd=round(val_usd, 2),
                val_khr=round(val_khr, 2),
                revenue_share_pct=round(item.get('revenue_share_pct', 0.0), 2),
                volume_share_pct=round(item.get('volume_share_pct', 0.0), 2),
                unit_price_usd_per_kg=round(unit_price, 3)
            )
        )

    # 3. HS4 Categories (Macro Level Reference)
    hs4_list = []
    for item in metrics.get('hs4_summary', []):
        code = clean_hs_code(item.get('hs4_code', ''), 4)
        t_en, t_km, d_en, d_km = get_hs4_official_name(code, item.get('hs4_desc', ''))
        val_usd = float(item.get('val_usd', 0.0) or 0.0)
        val_khr = float(item.get('val_khr', val_usd * exchange_rate) or 0.0)
        weight_ton = float(item.get('weight_ton', 0.0) or 0.0)
        weight_kg = float(item.get('weight_kg', 0.0) or (weight_ton * 1000.0))
        
        hs4_list.append(
            Hs4CategorySummary(
                hs4_code=code,
                hs4_desc=item.get('hs4_official_title') or t_en,
                official_title=item.get('hs4_official_title') or t_en,
                title_en=item.get('hs4_title_en') or t_en,
                title_km=item.get('hs4_title_km') or t_km,
                full_desc_en=item.get('hs4_full_desc_en') or d_en,
                full_desc_km=item.get('hs4_full_desc_km') or d_km,
                weight_tonnes=round(weight_ton, 2),
                weight_kg=round(weight_kg, 2),
                val_usd=round(val_usd, 2),
                val_khr=round(val_khr, 2),
                revenue_share_pct=round(item.get('revenue_share_pct', 0.0), 2),
                volume_share_pct=round(item.get('volume_share_pct', 0.0), 2),
                unit_price_usd_per_kg=0.0
            )
        )

    # 4. Market Share Table Data
    market_share_table = []
    for item in metrics.get('country_summary', []):
        raw_c = item.get('country', 'Other')
        c_info = get_country_info(raw_c)
        c_en = item.get('country_en') or c_info.get('EN') or raw_c
        c_kh = item.get('country_kh') or c_info.get('Canonical_KH') or raw_c
        c_iso = item.get('country_iso3') or c_info.get('ISO') or 'OTH'
        val_usd = float(item.get('val_usd', 0.0) or 0.0)
        val_khr = float(item.get('val_khr', val_usd * exchange_rate) or 0.0)
        weight_ton = float(item.get('weight_ton', 0.0) or 0.0)
        weight_kg = float(item.get('weight_kg', 0.0) or (weight_ton * 1000.0))
        rev_share = float(item.get('revenue_share_pct', item.get('share_pct', 0.0)) or 0.0)
        vol_share = float(item.get('volume_share_pct', 0.0) or 0.0)
        unit_price = item.get('unit_price_usd_per_kg')
        if unit_price is None:
            unit_price = (val_usd / weight_kg) if weight_kg > 0 else 0.0

        market_share_table.append(
            MarketShareItem(
                country=c_en,
                country_en=c_en,
                country_kh=c_kh,
                country_iso3=c_iso,
                val_usd=round(val_usd, 2),
                val_khr=round(val_khr, 2),
                weight_ton=round(weight_ton, 2),
                weight_kg=round(weight_kg, 2),
                revenue_share_pct=round(rev_share, 2),
                volume_share_pct=round(vol_share, 2),
                unit_price_usd_per_kg=round(unit_price, 3)
            )
        )
    
    # 5. Charts Configuration
    # Visual 1: HS8 Commodities Donut Chart
    commodity_chart_data = []
    for item in metrics.get('commodity_multi', metrics.get('hs8_commodities', [])):
        code = clean_hs_code(item.get('hs8_code', ''), 8)
        hs4 = clean_hs_code(item.get('hs4_code', ''), 4)
        info = get_hs8_product_info(code) if code else {}
        name_en = item.get('name_en') or item.get('product_name') or info.get('name_en') or f"HS {code}"
        name_km = item.get('name_km') or item.get('name_kh') or info.get('name_kh') or name_en
        cat_en = item.get('category_en') or info.get('category_en') or 'Other Agricultural'
        cat_km = item.get('category_km') or item.get('category_kh') or info.get('category_kh') or 'កសិផលផ្សេងៗ'
        val_usd = float(item.get('val_usd', 0.0) or 0.0)
        weight_ton = float(item.get('weight_ton', 0.0) or 0.0)
        weight_kg = float(item.get('weight_kg', 0.0) or (weight_ton * 1000.0))
        unit_price = item.get('unit_price_usd_per_kg')
        if unit_price is None:
            unit_price = (val_usd / weight_kg) if weight_kg > 0 else 0.0

        commodity_chart_data.append({
            'name': name_en,
            'name_km': name_km,
            'hs8_code': code,
            'hs4_code': hs4,
            'category_en': cat_en,
            'category_km': cat_km,
            'year': int(item['year']) if 'year' in item and pd.notna(item['year']) else None,
            'country': item.get('country', 'ALL'),
            'value': round(val_usd / 1e6, 3),
            'val_usd': round(val_usd, 2),
            'weight_ton': round(weight_ton, 2),
            'weight_kg': round(weight_kg, 2),
            'unit_price_usd_per_kg': round(unit_price, 3),
            'revenue_share_pct': round(item.get('revenue_share_pct', 0.0), 2),
            'volume_share_pct': round(item.get('volume_share_pct', 0.0), 2),
            'label': name_en
        })

    # Visual 2: Destination Countries Horizontal Bar Chart
    country_chart_data = []
    for item in metrics.get('country_multi', metrics.get('country_summary', [])):
        raw_c = item.get('country', 'Other')
        c_info = get_country_info(raw_c)
        c_en = item.get('country_en') or c_info.get('EN') or raw_c
        c_kh = item.get('country_kh') or c_info.get('Canonical_KH') or raw_c
        c_iso = item.get('country_iso3') or c_info.get('ISO') or 'OTH'
        val_usd = float(item.get('val_usd', 0.0) or 0.0)
        val_khr = float(item.get('val_khr', val_usd * exchange_rate) or 0.0)
        weight_ton = float(item.get('weight_ton', 0.0) or 0.0)
        weight_kg = float(item.get('weight_kg', 0.0) or (weight_ton * 1000.0))
        rev_share = float(item.get('revenue_share_pct', item.get('share_pct', 0.0)) or 0.0)
        vol_share = float(item.get('volume_share_pct', 0.0) or 0.0)

        country_chart_data.append({
            'name': c_en,
            'country': c_en,
            'country_kh': c_kh,
            'iso3': c_iso,
            'hs8_code': clean_hs_code(item.get('hs8_code', ''), 8),
            'hs4_code': item.get('hs4_code'),
            'year': item.get('year'),
            'value': round(val_usd / 1e6, 3),
            'val_usd': round(val_usd, 2),
            'val_khr': round(val_khr, 2),
            'weight_ton': round(weight_ton, 2),
            'weight_kg': round(weight_kg, 2),
            'revenue_share_pct': round(rev_share, 2),
            'volume_share_pct': round(vol_share, 2)
        })

    # Visual 3: Top 10 Market Share Table
    market_share_table_data = []
    for item in metrics.get('country_multi', metrics.get('country_summary', [])):
        raw_c = item.get('country', 'Other')
        c_info = get_country_info(raw_c)
        c_en = item.get('country_en') or c_info.get('EN') or raw_c
        c_kh = item.get('country_kh') or c_info.get('Canonical_KH') or raw_c
        c_iso = item.get('country_iso3') or c_info.get('ISO') or 'OTH'
        val_usd = float(item.get('val_usd', 0.0) or 0.0)
        val_khr = float(item.get('val_khr', val_usd * exchange_rate) or 0.0)
        weight_ton = float(item.get('weight_ton', 0.0) or 0.0)
        weight_kg = float(item.get('weight_kg', 0.0) or (weight_ton * 1000.0))
        rev_share = float(item.get('revenue_share_pct', item.get('share_pct', 0.0)) or 0.0)
        vol_share = float(item.get('volume_share_pct', 0.0) or 0.0)
        unit_price = item.get('unit_price_usd_per_kg')
        if unit_price is None:
            unit_price = (val_usd / weight_kg) if weight_kg > 0 else 0.0

        market_share_table_data.append({
            'country': c_en,
            'country_en': c_en,
            'country_kh': c_kh,
            'country_iso3': c_iso,
            'hs8_code': clean_hs_code(item.get('hs8_code', ''), 8),
            'year': int(item['year']) if 'year' in item and pd.notna(item['year']) else None,
            'hs4_code': item.get('hs4_code'),
            'val_usd': round(val_usd, 2),
            'val_million_usd': round(val_usd / 1e6, 3),
            'val_khr': round(val_khr, 2),
            'weight_ton': round(weight_ton, 2),
            'weight_kg': round(weight_kg, 2),
            'revenue_share_pct': round(rev_share, 2),
            'volume_share_pct': round(vol_share, 2),
            'unit_price_usd_per_kg': round(unit_price, 3)
        })

    # Visual 4: Monthly Export Dynamics Line Chart
    seasonality_chart_data = [
        {
            'name': item.get('yyyy_mm', ''),
            'yyyy_mm': item.get('yyyy_mm', ''),
            'hs8_code': clean_hs_code(item.get('hs8_code', ''), 8),
            'hs4_code': item.get('hs4_code'),
            'country': item.get('country'),
            'year': item.get('year'),
            'weight_kton': round(float(item.get('weight_kton', 0.0) or 0.0), 4),
            'val_million_usd': round(float(item.get('val_million_usd', 0.0) or 0.0), 4),
            'val_usd': round(float(item.get('val_usd', 0.0) or 0.0), 2),
            'weight_ton': round(float(item.get('weight_ton', item.get('weight_kg', 0.0)/1000.0) or 0.0), 2)
        } 
        for item in metrics.get('monthly_multi', metrics.get('monthly_summary', []))
    ]
    
    level1_charts = [
        ChartConfig(
            chart_id="chart_commodity_share",
            chart_type="DONUT",
            title="Commodities Export Volume & Revenue",
            data=commodity_chart_data,
            ai_meaning=AiMeaning(**ai_insights.get('commodity_bar_meaning', {
                'explanation': 'This donut chart visualizes the export volume and revenue contribution across major 8-digit HS8 agricultural commodities.',
                'key_takeaway': 'Leading agricultural commodities account for the majority of export volume and revenue.',
                'action': 'Expand local processing facilities to convert raw crop volumes into high-value processed products.'
            }))
        ),
        ChartConfig(
            chart_id="chart_market_share",
            chart_type="HORIZONTAL_BAR",
            title="Top Destination Countries Revenue ($M USD)",
            data=country_chart_data,
            ai_meaning=AiMeaning(**ai_insights.get('country_donut_meaning', {
                'explanation': 'This horizontal bar chart displays export revenue ranking across destination partner countries.',
                'key_takeaway': 'Regional buyers absorb the vast majority of exported agricultural value.',
                'action': 'Negotiate direct export corridors to diversify destination markets.'
            }))
        ),
        ChartConfig(
            chart_id="chart_market_share_table",
            chart_type="TABLE",
            title="Top 10 Market Share",
            data=market_share_table_data,
            ai_meaning=AiMeaning(**ai_insights.get('market_share_table_meaning', ai_insights.get('price_jump_meaning', {
                'explanation': 'This table summarizes market share across top destination countries by volume and revenue.',
                'key_takeaway': 'The top two regional partners account for the largest shares of total agricultural exports.',
                'action': 'Expand direct market linkages with international buyers to capture higher export margins.'
            })))
        ),
        ChartConfig(
            chart_id="chart_seasonality",
            chart_type="LINE",
            title="Volume and Revenue by Months",
            data=seasonality_chart_data,
            ai_meaning=AiMeaning(**ai_insights.get('seasonality_line_meaning', {
                'explanation': 'This dual-axis time-series chart tracks monthly export volume and revenue across the reporting timeline.',
                'key_takeaway': 'Export performance peaks sharply during Q1 harvest seasons before tapering in Q3/Q4.',
                'action': 'Invest in cold-chain and warehousing infrastructure to stabilize supply and prices year-round.'
            }))
        )
    ]
    
    return DashboardPayload(
        session_id=session_id,
        is_valid_trade_data=True,
        exchange_rate=exchange_rate,
        exchange_rate_info=exchange_rate_info,
        begin_date=metrics.get('begin_date'),
        end_date=metrics.get('end_date'),
        available_years=metrics.get('available_years', []),
        available_countries=metrics.get('available_countries', []),
        summary_kpis=summary_kpis,
        hs8_commodities=hs8_list,
        hs4_categories=hs4_list,
        market_share_table=market_share_table,
        level1_charts=level1_charts,
        hhi_risk_score=round(metrics['hhi_score'], 1),
        is_high_risk=metrics['is_high_risk'],
        executive_strategy=ai_insights.get('executive_strategy', []),
        commodity_details=metrics.get('commodity_details', {}),
        commodity_list=[CommodityListItem(**item) for item in metrics.get('commodity_list', [])],
    )

@router.post("/upload", response_model=DashboardPayload)
async def upload_file(
    file: UploadFile = File(...),
    exchange_rate: Optional[float] = Form(None)
):
    session_id = str(uuid.uuid4())
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
        return DashboardPayload(
            session_id=session_id,
            is_valid_trade_data=False,
            validation_message=msg,
            exchange_rate=rate_val,
            exchange_rate_info=rate_info
        )
        
    # 3. 5-Stage ETL Processing with Live Exchange Rate
    df_clean, metrics = ETLService.process_trade_data(df_raw, col_map, exchange_rate=rate_val)
    
    # 4. DuckDB Staging
    duckdb_service.register_dataset(session_id, df_clean)
    
    # 5. AI Synthesis
    ai_insights = ai_service.generate_chart_meanings_and_strategy(metrics)
    
    # 6. Cache in Session Store
    SESSION_STORE[session_id] = {
        'df_clean': df_clean,
        'metrics': metrics,
        'col_map': col_map
    }
    
    payload = build_dashboard_payload(session_id, metrics, rate_val, ai_insights, exchange_rate_info=rate_info)
    
    # Store in Redis
    redis_service.set_cached_dashboard(rate_val, payload.model_dump())
    
    return payload
