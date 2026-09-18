from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# --- Exchange Rate Models ---
class ExchangeRateInfo(BaseModel):
    rate: float = 4000.0
    is_realtime: bool = False
    currency: str = "USD"
    valid_date: Optional[str] = None
    source: str = "Default Fallback (4,000 KHR/USD)"
    error_message: Optional[str] = None

# --- Request Models ---
class RecalculateRequest(BaseModel):
    session_id: Optional[str] = "master"
    exchange_rate: Optional[float] = Field(default=None, description="KHR to 1 USD exchange rate (defaults to real-time MEF rate)")

class ChatRequest(BaseModel):
    session_id: Optional[str] = "master"
    question: str
    exchange_rate: Optional[float] = Field(default=None, description="KHR to 1 USD exchange rate (defaults to real-time MEF rate)")

# --- Sub-Schemas for Response ---
class KpiMetric(BaseModel):
    label: str
    value: str
    numeric_val: float
    unit: str
    description: str

class AiMeaning(BaseModel):
    explanation: str
    key_takeaway: str
    action: str

class ChartConfig(BaseModel):
    chart_id: str
    chart_type: str  # 'HORIZONTAL_BAR', 'DONUT', 'LINE', 'PAIRED_BAR'
    title: str
    data: List[Dict[str, Any]]
    ai_meaning: Optional[AiMeaning] = None

class Hs4CategorySummary(BaseModel):
    hs4_code: str
    hs4_desc: str
    official_title: Optional[str] = None
    title_en: Optional[str] = None
    title_km: Optional[str] = None
    full_desc_en: Optional[str] = None
    full_desc_km: Optional[str] = None
    weight_tonnes: float
    val_usd: float
    val_khr: float
    revenue_share_pct: float
    volume_share_pct: float
    unit_price_usd_per_kg: float

class Hs8SubProductSummary(BaseModel):
    hs8_code: str
    hs8_desc: str
    product_name: Optional[str] = None
    name_en: Optional[str] = None
    name_km: Optional[str] = None
    hs4_code: str
    weight_tonnes: float
    val_usd: float
    unit_price_usd_per_kg: float

class CommodityListItem(BaseModel):
    hs8_code: str
    hs4_code: str
    name_en: str
    name_km: str
    val_usd: float
    weight_kg: float

class CategoryDetailPayload(BaseModel):
    hs4_code: str
    hs4_desc: str
    sub_products: List[Hs8SubProductSummary]
    top_destinations: List[Dict[str, Any]]
    charts: List[ChartConfig]
    ai_strategy: Optional[str] = None

# --- Main Dashboard Payload ---
class DashboardPayload(BaseModel):
    session_id: str
    is_valid_trade_data: bool
    validation_message: Optional[str] = None
    exchange_rate: float = 4000.0
    exchange_rate_info: Optional[ExchangeRateInfo] = None
    begin_date: Optional[str] = None
    end_date: Optional[str] = None
    available_years: List[int] = []
    available_countries: List[str] = []
    summary_kpis: List[KpiMetric] = []
    hs4_categories: List[Hs4CategorySummary] = []
    level1_charts: List[ChartConfig] = []
    hhi_risk_score: float = 0.0
    is_high_risk: bool = False
    executive_strategy: List[str] = []
    category_details: Dict[str, CategoryDetailPayload] = {}
    commodity_details: Dict[str, Any] = {}
    commodity_list: List[CommodityListItem] = []

class ChatResponse(BaseModel):
    question: str
    answer: str
    sql_executed: Optional[str] = None
    data_points: Optional[List[Dict[str, Any]]] = None

# --- Admin Models ---
class UploadHistoryItem(BaseModel):
    filename: str
    rows_inserted: int
    rows_updated: int
    total_records: int
    period_range: Optional[str] = None
    uploaded_at: str

class AdminUploadResponse(BaseModel):
    success: bool
    message: str
    rows_inserted: int
    rows_updated: int
    total_records: int
    reporting_period: str
    exchange_rate_info: Optional[ExchangeRateInfo] = None
    dashboard_payload: Optional[DashboardPayload] = None
    upload_history: List[UploadHistoryItem] = []

class AdminStatusResponse(BaseModel):
    total_records: int
    total_export_val_usd: float
    total_weight_tonnes: float
    reporting_period: str
    hs4_chapters_count: int
    last_updated: str
    exchange_rate_info: Optional[ExchangeRateInfo] = None
    upload_history: List[UploadHistoryItem] = []
