import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.etl_service import ETLService
from app.services.duckdb_service import duckdb_service
from app.services.ai_service import ai_service
from app.services.exchange_rate_service import exchange_rate_service, ExchangeRateInfo
from app.models.schemas import (
    DashboardPayload, KpiMetric, Hs4CategorySummary, 
    Hs8SubProductSummary, CategoryDetailPayload, ChartConfig, AiMeaning, CommodityListItem
)

router = APIRouter()

# In-memory store for active session dataframes & raw metrics
SESSION_STORE = {}

def build_dashboard_payload(session_id: str, metrics: dict, exchange_rate: float, ai_insights: dict, exchange_rate_info: Optional[ExchangeRateInfo] = None) -> DashboardPayload:
    total_val_usd = metrics['total_val_usd']
    total_val_khr = metrics['total_val_khr']
    total_weight_ton = metrics['total_weight_ton']
    overall_avg_price = metrics['overall_avg_price_usd_per_kg']
    
    active_countries_count = len(metrics.get('country_summary', []))
    total_hs8_count = len(metrics.get('hs8_summary', []))
    
    # 1. KPI Cards
    summary_kpis = [
        KpiMetric(
            label="Total Value ($)",
            value=f"${total_val_usd/1e6:,.2f} Million USD",
            numeric_val=total_val_usd,
            unit="USD",
            description=f"Recalculated at $1 USD = {exchange_rate:,.0f} KHR"
        ),
        KpiMetric(
            label="Total Value (KHR)",
            value=f"៛{total_val_khr/1e9:,.2f} Billion KHR",
            numeric_val=total_val_khr,
            unit="KHR",
            description="Raw trade currency total"
        ),
        KpiMetric(
            label="Total Volume",
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
    
    # 2. HS4 Categories (Level 1)
    hs4_list = [
        Hs4CategorySummary(
            hs4_code=item['hs4_code'],
            hs4_desc=item['hs4_desc'],
            official_title=item.get('hs4_official_title', item['hs4_desc']),
            title_en=item.get('hs4_title_en', item.get('hs4_official_title', item['hs4_desc'])),
            title_km=item.get('hs4_title_km', ''),
            full_desc_en=item.get('hs4_full_desc_en', item.get('hs4_full_desc', '')),
            full_desc_km=item.get('hs4_full_desc_km', ''),
            weight_tonnes=round(item['weight_ton'], 2),
            val_usd=round(item['val_usd'], 2),
            val_khr=round(item['val_khr'], 2),
            revenue_share_pct=round(item['revenue_share_pct'], 2),
            volume_share_pct=round(item['volume_share_pct'], 2),
            unit_price_usd_per_kg=round(item['unit_price_usd_per_kg'], 3)
        )
        for item in metrics['hs4_summary']
    ]
    
    # 3. Level 1 Charts (Clean HS 4-digit code on axis, official product title in tooltips)
    commodity_chart_data = [
        {
            'name': f"HS {item['hs4_code']}",
            'hs4_code': item['hs4_code'],
            'year': int(item['year']),
            'country': item['country'],
            'value': round(item['val_usd']/1e6, 3),
            'val_usd': round(item['val_usd'], 2),
            'weight_ton': round(item['weight_ton'], 2),
            'label': item.get('hs4_official_title', ''),
            'is_chapter': True
        } 
        for item in metrics.get('hs4_multi', metrics['hs4_summary'])
    ]

    country_chart_data = [
        {
            'name': item['country'],
            'country': item['country'],
            'hs4_code': item.get('hs4_code'),
            'year': item.get('year'),
            'value': round(item['val_usd']/1e6, 3),
            'val_usd': round(item['val_usd'], 2),
            'weight_ton': round(item.get('weight_ton', 0), 2)
        } 
        for item in metrics.get('country_multi', metrics['country_summary'])
    ]

    seasonality_chart_data = [
        {
            'name': item['yyyy_mm'],
            'yyyy_mm': item['yyyy_mm'],
            'hs4_code': item.get('hs4_code'),
            'country': item.get('country'),
            'year': item.get('year'),
            'weight_kton': round(item.get('weight_kton', 0), 4),
            'val_million_usd': round(item.get('val_million_usd', 0), 4),
            'val_usd': round(item.get('val_usd', 0), 2),
            'weight_ton': round(item.get('weight_ton', item.get('weight_kg', 0)/1000.0), 2)
        } 
        for item in metrics.get('monthly_multi', metrics['monthly_summary'])
    ]
    
    # Dynamic Price Jump Data (Computed strictly from uploaded 8-digit tariff lines)
    # Dynamic Raw vs Processed Comparison Data (Supporting both Value $M USD and Volume Tonnes metrics)
    PAIRS_CONFIG = [
        {
            'hs4_code': '0801',
            'category': 'HS 0801 - Cashew Nuts & Coconuts',
            'raw_hs8': {'08013100'},
            'proc_hs8': {'08013200'},
            'raw_label': 'In-shell (Raw)',
            'processed_label': 'Shelled (Processed)'
        },
        {
            'hs4_code': '0804',
            'category': 'HS 0804 - Fresh & Dried Mangoes',
            'raw_hs8': {'08045021'},
            'proc_hs8': {'08045022'},
            'raw_label': 'Fresh Mango',
            'processed_label': 'Dried Mango'
        },
        {
            'hs4_code': '0904',
            'category': 'HS 0904 - Pepper & Chili (Capsicum)',
            'raw_hs8': {'09041120', '09041110', '09041190', '09042110'},
            'proc_hs8': {'09041220', '09041210', '09041290', '09042210'},
            'raw_label': 'Whole Pepper',
            'processed_label': 'Ground Pepper'
        },
        {
            'hs4_code': '0910',
            'category': 'HS 0910 - Ginger, Turmeric & Spices',
            'raw_hs8': {'09101100'},
            'proc_hs8': {'09101200'},
            'raw_label': 'Whole Ginger',
            'processed_label': 'Crushed Ginger'
        }
    ]

    price_jump_data = []
    raw_multi = metrics.get('commodity_multi', [])
    if raw_multi:
        grouped_pairs = {}
        for row in raw_multi:
            code8 = str(row.get('hs8_code', '')).zfill(8)
            hs4 = str(row.get('hs4_code', '')).zfill(4)
            year = row.get('year')
            country = row.get('country')
            key = (hs4, year, country)
            if key not in grouped_pairs:
                grouped_pairs[key] = {
                    'raw_val_usd': 0.0,
                    'raw_weight_ton': 0.0,
                    'proc_val_usd': 0.0,
                    'proc_weight_ton': 0.0
                }
            
            for pair in PAIRS_CONFIG:
                if pair['hs4_code'] == hs4:
                    if code8 in pair['raw_hs8']:
                        grouped_pairs[key]['raw_val_usd'] += float(row.get('val_usd', 0))
                        grouped_pairs[key]['raw_weight_ton'] += float(row.get('weight_ton', 0))
                    elif code8 in pair['proc_hs8']:
                        grouped_pairs[key]['proc_val_usd'] += float(row.get('val_usd', 0))
                        grouped_pairs[key]['proc_weight_ton'] += float(row.get('weight_ton', 0))

        for (hs4, year, country), vals in grouped_pairs.items():
            pair = next((p for p in PAIRS_CONFIG if p['hs4_code'] == hs4), None)
            if not pair:
                continue
            if vals['raw_val_usd'] > 0 or vals['proc_val_usd'] > 0 or vals['raw_weight_ton'] > 0 or vals['proc_weight_ton'] > 0:
                price_jump_data.append({
                    'hs4_code': hs4,
                    'category': pair['category'],
                    'raw_label': pair['raw_label'],
                    'processed_label': pair['processed_label'],
                    'year': int(year) if year is not None else None,
                    'country': country,
                    'raw_val_usd': round(vals['raw_val_usd'], 2),
                    'raw_weight_ton': round(vals['raw_weight_ton'], 2),
                    'proc_val_usd': round(vals['proc_val_usd'], 2),
                    'proc_weight_ton': round(vals['proc_weight_ton'], 2),
                    'Raw_Val': round(vals['raw_val_usd'] / 1e6, 3),
                    'Processed_Val': round(vals['proc_val_usd'] / 1e6, 3),
                    'Raw_Tonnes': round(vals['raw_weight_ton'], 2),
                    'Processed_Tonnes': round(vals['proc_weight_ton'], 2)
                })

    if not price_jump_data:
        hs8_obj_map = {str(item.get('hs8_code', '')).zfill(8): item for item in metrics.get('hs8_summary', [])}
        for pair in PAIRS_CONFIG:
            r_val = sum(float(hs8_obj_map[c].get('val_usd', 0)) for c in pair['raw_hs8'] if c in hs8_obj_map)
            r_w = sum(float(hs8_obj_map[c].get('weight_ton', 0)) for c in pair['raw_hs8'] if c in hs8_obj_map)
            p_val = sum(float(hs8_obj_map[c].get('val_usd', 0)) for c in pair['proc_hs8'] if c in hs8_obj_map)
            p_w = sum(float(hs8_obj_map[c].get('weight_ton', 0)) for c in pair['proc_hs8'] if c in hs8_obj_map)
            if r_val > 0 or p_val > 0 or r_w > 0 or p_w > 0:
                price_jump_data.append({
                    'hs4_code': pair['hs4_code'],
                    'category': pair['category'],
                    'raw_label': pair['raw_label'],
                    'processed_label': pair['processed_label'],
                    'raw_val_usd': round(r_val, 2),
                    'raw_weight_ton': round(r_w, 2),
                    'proc_val_usd': round(p_val, 2),
                    'proc_weight_ton': round(p_w, 2),
                    'Raw_Val': round(r_val / 1e6, 3),
                    'Processed_Val': round(p_val / 1e6, 3),
                    'Raw_Tonnes': round(r_w, 2),
                    'Processed_Tonnes': round(p_w, 2)
                })
    
    level1_charts = [
        ChartConfig(
            chart_id="chart_commodity_share",
            chart_type="HORIZONTAL_BAR",
            title="Export Revenue by HS 4-Digit Category ($M USD)",
            data=commodity_chart_data,
            ai_meaning=AiMeaning(**ai_insights['commodity_bar_meaning'])
        ),
        ChartConfig(
            chart_id="chart_market_share",
            chart_type="DONUT",
            title="Destination Country Share ($M USD)",
            data=country_chart_data,
            ai_meaning=AiMeaning(**ai_insights['country_donut_meaning'])
        ),
        ChartConfig(
            chart_id="chart_price_jump",
            chart_type="PAIRED_BAR",
            title="Value Jump: Raw vs Processed Export Price ($/kg)",
            data=price_jump_data,
            ai_meaning=AiMeaning(**ai_insights['price_jump_meaning'])
        ),
        ChartConfig(
            chart_id="chart_seasonality",
            chart_type="LINE",
            title="Monthly Export Dynamics: Weight (kTonnes) vs Value ($M USD)",
            data=seasonality_chart_data,
            ai_meaning=AiMeaning(**ai_insights['seasonality_line_meaning'])
        )
    ]
    
    # 4. Level 2 Category Drill-Down Details
    category_details = {}
    for hs4 in metrics['hs4_summary']:
        code = hs4['hs4_code']
        cat_total_val = float(hs4['val_usd'])
        cat_total_khr = float(hs4.get('val_khr', hs4['val_usd'] * exchange_rate))
        cat_total_ton = float(hs4['weight_ton'])
        
        # Sub-products for this chapter
        sub_prods = []
        for item in metrics['hs8_summary']:
            if item['hs4_code'] == code:
                sp_val = float(item['val_usd'])
                sp_ton = float(item['weight_ton'])
                sp_khr = sp_val * exchange_rate
                sp_share = (sp_val / max(0.001, cat_total_val)) * 100.0
                sp_price_usd = float(item['unit_price_usd_per_kg'])
                sp_price_khr = sp_price_usd * exchange_rate
                sub_prods.append(
                    Hs8SubProductSummary(
                        hs8_code=item['hs8_code'],
                        hs8_desc=item['hs8_desc'],
                        product_name=item.get('product_name', item['hs8_desc']),
                        name_en=item.get('name_en', item.get('product_name', item['hs8_desc'])),
                        name_km=item.get('name_km', ''),
                        hs4_code=item['hs4_code'],
                        weight_tonnes=round(sp_ton, 2),
                        val_usd=round(sp_val, 2),
                        val_khr=round(sp_khr, 2),
                        unit_price_usd_per_kg=round(sp_price_usd, 3),
                        unit_price_khr_per_kg=round(sp_price_khr, 1),
                        revenue_share_pct=round(sp_share, 2)
                    )
                )
        sub_prods.sort(key=lambda x: x.val_usd, reverse=True)
        
        # Chapter Destination Markets Breakdown
        cat_country_rows = [c for c in metrics.get('country_multi', []) if c.get('hs4_code') == code]
        cat_country_map = {}
        for row in cat_country_rows:
            ctry = row['country']
            if ctry not in cat_country_map:
                cat_country_map[ctry] = {'country': ctry, 'val_usd': 0.0, 'val_khr': 0.0, 'weight_kg': 0.0}
            cat_country_map[ctry]['val_usd'] += float(row.get('val_usd', 0))
            cat_country_map[ctry]['weight_kg'] += float(row.get('weight_ton', 0)) * 1000.0
        
        top_destinations = []
        for ctry, cvals in cat_country_map.items():
            c_val = cvals['val_usd']
            c_share = (c_val / max(0.001, cat_total_val)) * 100.0
            top_destinations.append({
                'country': ctry,
                'val_usd': round(c_val, 2),
                'val_khr': round(c_val * exchange_rate, 2),
                'weight_kg': round(cvals['weight_kg'], 2),
                'share_pct': round(c_share, 2)
            })
        top_destinations.sort(key=lambda x: x['val_usd'], reverse=True)
        
        # Chapter Monthly Seasonality
        cat_monthly_rows = [m for m in metrics.get('monthly_multi', []) if m.get('hs4_code') == code]
        cat_month_map = {}
        for row in cat_monthly_rows:
            ym = row['yyyy_mm']
            if ym not in cat_month_map:
                cat_month_map[ym] = {'yyyy_mm': ym, 'val_usd': 0.0, 'weight_kg': 0.0}
            cat_month_map[ym]['val_usd'] += float(row.get('val_usd', 0))
            cat_month_map[ym]['weight_kg'] += float(row.get('weight_ton', 0)) * 1000.0
            
        cat_monthly_trend = []
        for ym in sorted(cat_month_map.keys()):
            m_val = cat_month_map[ym]['val_usd']
            m_kg = cat_month_map[ym]['weight_kg']
            cat_monthly_trend.append({
                'yyyy_mm': ym,
                'val_usd': round(m_val, 2),
                'val_khr': round(m_val * exchange_rate, 2),
                'weight_kg': round(m_kg, 2),
                'price_usd_per_kg': round(m_val / max(1.0, m_kg), 3),
                'price_khr_per_kg': round((m_val * exchange_rate) / max(1.0, m_kg), 1)
            })

        # Chapter HHI
        cat_hhi = sum((d['share_pct'])**2 for d in top_destinations)
        
        # Chapter Charts
        subprod_chart_data = [
            {
                'name': sp.name_en or sp.product_name or sp.hs8_code,
                'hs8_code': sp.hs8_code,
                'value': round(sp.val_usd / 1e6, 3) if sp.val_usd >= 1e6 else round(sp.val_usd / 1e3, 2),
                'val_usd': sp.val_usd,
                'weight_ton': sp.weight_tonnes,
                'label': sp.name_km or sp.hs8_desc
            }
            for sp in sub_prods
        ]
        
        dest_chart_data = [
            {
                'name': d['country'],
                'country': d['country'],
                'value': round(d['val_usd'] / 1e6, 3) if d['val_usd'] >= 1e6 else round(d['val_usd'] / 1e3, 2),
                'val_usd': d['val_usd'],
                'weight_ton': round(d['weight_kg'] / 1000.0, 2)
            }
            for d in top_destinations[:8]
        ]
        
        seasonality_data = [
            {
                'name': m['yyyy_mm'],
                'yyyy_mm': m['yyyy_mm'],
                'value': round(m['val_usd'] / 1e6, 3) if m['val_usd'] >= 1e6 else round(m['val_usd'] / 1e3, 2),
                'val_usd': m['val_usd'],
                'weight_ton': round(m['weight_kg'] / 1000.0, 2)
            }
            for m in cat_monthly_trend
        ]
        
        top_sp_name = sub_prods[0].name_en if sub_prods else 'Top commodity'
        top_sp_share = sub_prods[0].revenue_share_pct if sub_prods else 0
        top_dest_name = top_destinations[0]['country'] if top_destinations else 'N/A'
        top_dest_share = top_destinations[0]['share_pct'] if top_destinations else 0

        charts = [
            ChartConfig(
                chart_id=f"chart_{code}_subprods",
                chart_type="HORIZONTAL_BAR",
                title=f"Sub-Products Export Revenue: HS {code}",
                data=subprod_chart_data,
                ai_meaning=AiMeaning(
                    explanation=f"Revenue breakdown across all {len(sub_prods)} 8-digit tariff lines in chapter HS {code}.",
                    key_takeaway=f"Leading commodity ({top_sp_name}) accounts for {top_sp_share}% of total chapter export value.",
                    action="Accelerate commercial processing infrastructure to expand premium product exports."
                )
            ),
            ChartConfig(
                chart_id=f"chart_{code}_destinations",
                chart_type="DONUT",
                title=f"Destination Markets for HS {code}",
                data=dest_chart_data,
                ai_meaning=AiMeaning(
                    explanation=f"Destination market distribution for chapter HS {code} (HHI Risk Score: {round(cat_hhi, 1)}).",
                    key_takeaway=f"Primary buyer is {top_dest_name} with {top_dest_share}% market share.",
                    action="Broaden direct export channels to premium consumer markets."
                )
            ),
            ChartConfig(
                chart_id=f"chart_{code}_seasonality",
                chart_type="LINE",
                title=f"Monthly Export Dynamics: HS {code}",
                data=seasonality_data,
                ai_meaning=AiMeaning(
                    explanation=f"Monthly export volume and revenue timeline for chapter HS {code}.",
                    key_takeaway="Harvest seasons generate high-volume spikes followed by off-season price premiums.",
                    action="Utilize cold-chain warehousing to stagger exports and capture peak off-season unit prices."
                )
            )
        ]
        
        # Add Raw vs Processed chart if applicable
        pair = next((p for p in PAIRS_CONFIG if p['hs4_code'] == code), None)
        if pair:
            pair_data = [item for item in price_jump_data if item.get('hs4_code') == code]
            if pair_data:
                charts.append(
                    ChartConfig(
                        chart_id=f"chart_{code}_pair",
                        chart_type="PAIRED_BAR",
                        title=f"Raw vs Processed Value Analysis: HS {code}",
                        data=pair_data,
                        ai_meaning=AiMeaning(
                            explanation=f"Value-added price spread between raw ({pair['raw_label']}) and processed ({pair['processed_label']}).",
                            key_takeaway="Processed products capture significantly higher margins per kilogram than raw commodities.",
                            action="Incentivize local agro-processing factories to capture higher value domestically."
                        )
                    )
                )

        category_details[code] = CategoryDetailPayload(
            hs4_code=code,
            hs4_desc=hs4['hs4_desc'],
            title_en=hs4.get('hs4_title_en', hs4.get('hs4_official_title', hs4['hs4_desc'])),
            title_km=hs4.get('hs4_title_km', ''),
            full_desc_en=hs4.get('hs4_full_desc_en', hs4.get('hs4_full_desc', '')),
            full_desc_km=hs4.get('hs4_full_desc_km', ''),
            total_val_usd=round(cat_total_val, 2),
            total_val_khr=round(cat_total_khr, 2),
            total_weight_ton=round(cat_total_ton, 2),
            avg_price_usd_per_kg=round(cat_total_val / max(1.0, cat_total_ton * 1000.0), 3),
            avg_price_khr_per_kg=round(cat_total_khr / max(1.0, cat_total_ton * 1000.0), 1),
            num_markets=len(top_destinations),
            hhi_score=round(cat_hhi, 1),
            revenue_share_pct=round(hs4.get('revenue_share_pct', 0), 2),
            sub_products=sub_prods,
            top_destinations=top_destinations,
            monthly_trend=cat_monthly_trend,
            charts=charts,
            ai_strategy=f"Strategic Focus for HS {code} ({hs4.get('hs4_title_en', hs4['hs4_desc'])}): Expand value-added processing for {top_sp_name} and diversify export destinations beyond {top_dest_name}."
        )

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
        hs4_categories=hs4_list,
        level1_charts=level1_charts,
        hhi_risk_score=round(metrics['hhi_score'], 1),
        is_high_risk=metrics['is_high_risk'],
        executive_strategy=ai_insights['executive_strategy'],
        category_details=category_details,
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
    
    # 5. AI Graph Insights & Executive Strategy
    ai_insights = ai_service.generate_chart_meanings_and_strategy(metrics)
    
    # Save session state
    SESSION_STORE[session_id] = {
        'df_clean': df_clean,
        'col_map': col_map,
        'metrics': metrics
    }
    
    return build_dashboard_payload(session_id, metrics, rate_val, ai_insights, exchange_rate_info=rate_info)
