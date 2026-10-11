export interface KpiMetric {
  label: string;
  value: string;
  numeric_val: number;
  unit: string;
  description: string;
}

export interface AiMeaning {
  explanation: string;
  key_takeaway: string;
  action: string;
}

export interface ChartConfig {
  chart_id: string;
  chart_type: 'HORIZONTAL_BAR' | 'DONUT' | 'LINE' | 'TABLE' | 'PAIRED_BAR';
  title: string;
  data: any[];
  ai_meaning?: AiMeaning;
}

export interface Hs8CommoditySummary {
  hs8_code: string;
  hs4_code: string;
  name_en: string;
  name_km: string;
  category_en: string;
  category_km: string;
  weight_tonnes: number;
  weight_kg?: number;
  val_usd: number;
  val_khr: number;
  revenue_share_pct: number;
  volume_share_pct: number;
  unit_price_usd_per_kg: number;
}

export interface Hs4CategorySummary {
  hs4_code: string;
  hs4_desc: string;
  official_title?: string;
  title_en?: string;
  title_km?: string;
  full_desc_en?: string;
  full_desc_km?: string;
  weight_tonnes: number;
  weight_kg?: number;
  val_usd: number;
  val_khr: number;
  revenue_share_pct: number;
  volume_share_pct: number;
  unit_price_usd_per_kg: number;
}

export interface MarketShareItem {
  country: string;
  country_en: string;
  country_kh: string;
  country_iso3: string;
  val_usd: number;
  val_khr: number;
  weight_ton: number;
  weight_kg?: number;
  revenue_share_pct: number;
  volume_share_pct: number;
  unit_price_usd_per_kg: number;
}

export interface CommodityListItem {
  hs8_code: string;
  hs4_code: string;
  name_en: string;
  name_km: string;
  val_usd: number;
  weight_kg: number;
}

export interface MarketBreakdownItem {
  country: string;
  val_usd: number;
  val_khr: number;
  weight_kg: number;
  share_pct: number;
}

export interface YearlyMarketItem {
  country: string;
  year: number;
  val_usd: number;
  val_khr: number;
  weight_kg: number;
}

export interface MonthlyTrendItem {
  yyyy_mm: string;
  val_usd: number;
  val_khr: number;
  weight_kg: number;
  price_usd_per_kg: number;
  price_khr_per_kg: number;
}

export interface RawVsProcessed {
  raw_hs8: string;
  processed_hs8: string;
  raw_name_en: string;
  raw_name_km: string;
  processed_name_en: string;
  processed_name_km: string;
  raw_val_usd: number;
  raw_weight_kg: number;
  raw_price_usd_per_kg: number;
  raw_price_khr_per_kg: number;
  proc_val_usd: number;
  proc_weight_kg: number;
  proc_price_usd_per_kg: number;
  proc_price_khr_per_kg: number;
}

export interface CommodityDetail {
  hs8_code: string;
  hs4_code: string;
  name_en: string;
  name_km: string;
  total_val_usd: number;
  total_val_khr: number;
  total_weight_kg: number;
  total_weight_ton: number;
  avg_price_usd_per_kg: number;
  avg_price_khr_per_kg: number;
  num_markets: number;
  total_transactions?: number;
  monthly_trend: MonthlyTrendItem[];
  market_breakdown: MarketBreakdownItem[];
  yearly_markets?: YearlyMarketItem[];
  raw_vs_processed: RawVsProcessed | null;
}

export interface ExchangeRateInfo {
  rate: number;
  is_realtime: boolean;
  currency: string;
  valid_date?: string | null;
  source: string;
  error_message?: string | null;
}

export interface DashboardPayload {
  publication?: { id: string; revision_id: string; start_month: string; end_month: string } | null;
  session_id: string;
  is_valid_trade_data: boolean;
  validation_message?: string;
  exchange_rate: number;
  exchange_rate_info?: ExchangeRateInfo;
  begin_date?: string;
  end_date?: string;
  available_years?: number[];
  available_countries?: string[];
  summary_kpis: KpiMetric[];
  hs8_commodities: Hs8CommoditySummary[];
  hs4_categories: Hs4CategorySummary[];
  market_share_table: MarketShareItem[];
  level1_charts: ChartConfig[];
  hhi_risk_score: number;
  is_high_risk: boolean;
  executive_strategy: string[];
  commodity_details: Record<string, CommodityDetail>;
  commodity_list: CommodityListItem[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
  sql?: string;
}
