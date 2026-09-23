import io
import datetime
from typing import Tuple, Dict, Any, List, Optional
import numpy as np
import pandas as pd
from app.services.hs_product_service import (
    clean_text,
    clean_hs_code,
    get_hs8_product_info,
    get_product_name,
    get_product_names_bilingual,
    get_hs4_official_name,
    get_country_info,
    get_raw_processed_pair,
    RAW_VS_PROCESSED_PAIRS
)

class ETLService:
    @staticmethod
    def inspect_and_load_file(file_contents: bytes, filename: str) -> pd.DataFrame:
        """Parses Excel or CSV files, dynamically detecting the true header row."""
        if filename.endswith('.csv'):
            df_raw = pd.read_csv(io.BytesIO(file_contents), encoding="utf-8-sig")
            return df_raw
            
        # For Excel (.xlsx, .xls) scan first 15 rows for header density
        df_scan = pd.read_excel(io.BytesIO(file_contents), nrows=15, header=None)
        best_header_idx = 0
        max_score = -1
        
        for idx, row in df_scan.iterrows():
            str_vals = [clean_text(v) for v in row.dropna() if clean_text(v) != '']
            score = len(str_vals) * (len(set(str_vals)) / max(1, len(str_vals)))
            if score > max_score:
                max_score = score
                best_header_idx = idx
                
        df = pd.read_excel(io.BytesIO(file_contents), header=best_header_idx)
        return df

    @staticmethod
    def resolve_period_overlaps(frames: List[pd.DataFrame]) -> pd.DataFrame:
        """
        Intelligently combines multiple DataFrames across periodic file drops.
        If multiple files report data for the same (Year, Month), selects the most
        complete batch (maximum row count), preventing duplicate batch stacking.
        """
        if not frames:
            return pd.DataFrame()
        if len(frames) == 1:
            return frames[0]

        all_periods = set()
        for frame in frames:
            if 'year' in frame.columns and 'month' in frame.columns:
                valid_rows = frame.dropna(subset=['year', 'month'])
                for _, r in valid_rows[['year', 'month']].drop_duplicates().iterrows():
                    try:
                        y = int(float(r['year']))
                        m = int(float(r['month']))
                        all_periods.add((y, m))
                    except (ValueError, TypeError):
                        continue

        if not all_periods:
            return pd.concat(frames, ignore_index=True)

        resolved_batches = []
        for y, m in sorted(all_periods):
            candidates = []
            for frame in frames:
                try:
                    subset = frame[
                        (pd.to_numeric(frame['year'], errors='coerce') == y) &
                        (pd.to_numeric(frame['month'], errors='coerce') == m)
                    ]
                    if not subset.empty:
                        candidates.append((len(subset), subset))
                except Exception:
                    continue

            if not candidates:
                continue

            candidates.sort(key=lambda x: x[0], reverse=True)
            resolved_batches.append(candidates[0][1])

        return pd.concat(resolved_batches, ignore_index=True)

    @staticmethod
    def validate_trade_schema(df: pd.DataFrame) -> Tuple[bool, str, Dict[str, str]]:
        """
        Validates whether the dataframe contains the required trade data columns:
        Year, Month, HS8, HS4, Description, Country, Weight, Value.
        """
        cols_lower = {clean_text(str(c)).lower(): c for c in df.columns}
        
        # Keyword mappings
        year_col = next((cols_lower[k] for k in cols_lower if any(y in k for y in ['ឆ្នាំ', 'year', 'yyyy'])), None)
        month_col = next((cols_lower[k] for k in cols_lower if any(m in k for m in ['ខែ', 'month', 'mm'])), None)
        hs8_col = next((cols_lower[k] for k in cols_lower if any(h in k for h in ['៨ខ្ទង់', 'hs8', '8-digit'])), None)
        hs4_col = next((cols_lower[k] for k in cols_lower if any(h in k for h in ['៤ខ្ទង់', 'hs4', '4-digit'])), None)
        desc_col = next((cols_lower[k] for k in cols_lower if any(d in k for d in ['បរិយាយ', 'description', 'desc'])), None)
        country_col = next((cols_lower[k] for k in cols_lower if any(c in k for c in ['ប្រទេស', 'country', 'destination', 'partner'])), None)
        weight_col = next((cols_lower[k] for k in cols_lower if any(w in k for w in ['ទម្ងន់', 'weight', 'kg', 'volume', 'tons'])), None)
        value_col = next((cols_lower[k] for k in cols_lower if any(v in k for v in ['តម្លៃ', 'value', 'riel', 'khr', 'usd'])), None)
        
        col_map = {
            'year': year_col,
            'month': month_col,
            'hs8': hs8_col,
            'hs4': hs4_col,
            'desc': desc_col,
            'country': country_col,
            'weight': weight_col,
            'value': value_col
        }
        
        missing = [k for k, v in col_map.items() if v is None]
        
        if len(missing) > 3:
            msg = f"This dataset is missing standard trade columns ({', '.join(missing)}). Please upload a valid Agricultural Trade dataset."
            return False, msg, col_map
            
        return True, "Dataset validated successfully.", col_map

    @staticmethod
    def process_trade_data(df: pd.DataFrame, col_map: Dict[str, str] = None, exchange_rate: float = 4000.0) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Cleans, normalizes, and computes metrics based on user-defined exchange rate."""
        df_clean = df.copy()
        
        # Standardize column names if col_map provided
        if col_map:
            rename_dict = {v: k for k, v in col_map.items() if v is not None}
            df_clean = df_clean.rename(columns=rename_dict)
        
        # Clean text across all string columns
        for col in df_clean.select_dtypes(include=['object', 'string']).columns:
            df_clean[col] = df_clean[col].apply(clean_text)

        # Fallback missing columns if any
        if 'year' not in df_clean.columns: df_clean['year'] = 2023
        if 'month' not in df_clean.columns: df_clean['month'] = 1
        if 'country' not in df_clean.columns: df_clean['country'] = 'Unknown'
        
        # Standardize Country Attributes
        def resolve_country(raw_c):
            info = get_country_info(raw_c)
            return info['EN'], info['Canonical_KH'], info['ISO']

        country_data = df_clean['country'].apply(resolve_country)
        df_clean['country_en'] = country_data.apply(lambda x: x[0])
        df_clean['country_kh'] = country_data.apply(lambda x: x[1])
        df_clean['country_iso3'] = country_data.apply(lambda x: x[2])
        # Use clean English country name as default primary country column
        df_clean['country'] = df_clean['country_en']

        # Clean numeric weight (kg) and value (KHR)
        if 'weight_kg' not in df_clean.columns or df_clean['weight_kg'].isnull().all():
            weight_src = df_clean['weight'] if 'weight' in df_clean.columns else 0
            df_clean['weight_kg'] = pd.to_numeric(
                weight_src.astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce'
            ).fillna(0.0)
        else:
            df_clean['weight_kg'] = pd.to_numeric(df_clean['weight_kg'], errors='coerce').fillna(0.0)
            
        if 'val_khr' not in df_clean.columns or df_clean['val_khr'].isnull().all():
            val_src = df_clean['value'] if 'value' in df_clean.columns else 0
            df_clean['val_khr'] = pd.to_numeric(
                val_src.astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce'
            ).fillna(0.0)
        else:
            df_clean['val_khr'] = pd.to_numeric(df_clean['val_khr'], errors='coerce').fillna(0.0)
        
        # Compute USD value dynamically based on exchange_rate input
        df_clean['val_usd'] = df_clean['val_khr'] / max(1.0, exchange_rate)
        
        # Format HS codes with fixed widths
        if 'hs4_code' not in df_clean.columns:
            hs4_src = df_clean['hs4'] if 'hs4' in df_clean.columns else '0000'
            df_clean['hs4_code'] = hs4_src.apply(lambda x: clean_hs_code(x, 4))
        else:
            df_clean['hs4_code'] = df_clean['hs4_code'].apply(lambda x: clean_hs_code(x, 4))
            
        if 'hs8_code' not in df_clean.columns:
            hs8_src = df_clean['hs8'] if 'hs8' in df_clean.columns else '00000000'
            df_clean['hs8_code'] = hs8_src.apply(lambda x: clean_hs_code(x, 8))
        else:
            df_clean['hs8_code'] = df_clean['hs8_code'].apply(lambda x: clean_hs_code(x, 8))
            
        if 'hs4_desc' not in df_clean.columns:
            desc_src = df_clean['desc'] if 'desc' in df_clean.columns else 'Agricultural Product'
            df_clean['hs4_desc'] = desc_src.astype(str).apply(clean_text)
            
        # Attach Human-Readable Product Name to dataframe
        df_clean['product_name'] = df_clean.apply(
            lambda r: get_product_name(r['hs8_code'], r['hs4_desc']), axis=1
        )
        
        # Summary Calculations
        total_weight_kg = df_clean['weight_kg'].sum()
        total_weight_ton = total_weight_kg / 1000.0
        total_val_khr = df_clean['val_khr'].sum()
        total_val_usd = df_clean['val_usd'].sum()
        overall_avg_price_usd_per_kg = total_val_usd / max(1.0, total_weight_kg)
        
        # 1. HS8 Commodity Aggregation (Primary Level)
        hs8_agg = df_clean.groupby(['hs8_code', 'hs4_code']).agg(
            weight_kg=('weight_kg', 'sum'),
            val_khr=('val_khr', 'sum'),
            val_usd=('val_usd', 'sum')
        ).reset_index()
        hs8_agg['weight_ton'] = hs8_agg['weight_kg'] / 1000.0
        
        hs8_agg['revenue_share_pct'] = (hs8_agg['val_usd'] / max(0.001, total_val_usd)) * 100.0
        hs8_agg['volume_share_pct'] = (hs8_agg['weight_kg'] / max(0.001, total_weight_kg)) * 100.0
        hs8_agg['unit_price_usd_per_kg'] = np.where(hs8_agg['weight_kg'] > 0, hs8_agg['val_usd'] / hs8_agg['weight_kg'], 0.0)

        hs8_details = hs8_agg['hs8_code'].apply(get_hs8_product_info)
        hs8_agg['name_en'] = hs8_details.apply(lambda d: d['name_en'])
        hs8_agg['name_km'] = hs8_details.apply(lambda d: d['name_kh'])
        hs8_agg['category_en'] = hs8_details.apply(lambda d: d['category_en'])
        hs8_agg['category_km'] = hs8_details.apply(lambda d: d['category_kh'])
        hs8_agg = hs8_agg.sort_values('val_usd', ascending=False)
        
        # 2. HS4 Chapter Aggregation (Macro Reference)
        hs4_agg = df_clean.groupby(['hs4_code']).agg(
            weight_kg=('weight_kg', 'sum'),
            val_khr=('val_khr', 'sum'),
            val_usd=('val_usd', 'sum')
        ).reset_index()
        hs4_agg['weight_ton'] = hs4_agg['weight_kg'] / 1000.0
        
        hs4_agg['revenue_share_pct'] = (hs4_agg['val_usd'] / max(0.001, total_val_usd)) * 100.0
        hs4_agg['volume_share_pct'] = (hs4_agg['weight_kg'] / max(0.001, total_weight_kg)) * 100.0
        hs4_agg['unit_price_usd_per_kg'] = np.where(hs4_agg['weight_kg'] > 0, hs4_agg['val_usd'] / hs4_agg['weight_kg'], 0.0)
        
        hs4_titles_en, hs4_titles_km, hs4_descs_en, hs4_descs_km = [], [], [], []
        for _, row in hs4_agg.iterrows():
            t_en, t_km, d_en, d_km = get_hs4_official_name(row['hs4_code'])
            hs4_titles_en.append(t_en)
            hs4_titles_km.append(t_km)
            hs4_descs_en.append(d_en)
            hs4_descs_km.append(d_km)

        hs4_agg['hs4_official_title'] = hs4_titles_en
        hs4_agg['hs4_title_en'] = hs4_titles_en
        hs4_agg['hs4_title_km'] = hs4_titles_km
        hs4_agg['hs4_full_desc_en'] = hs4_descs_en
        hs4_agg['hs4_full_desc_km'] = hs4_descs_km
        hs4_agg = hs4_agg.sort_values('val_usd', ascending=False)

        # 3. Country & Market Concentration (HHI & Market Share Table)
        country_agg = df_clean.groupby(['country', 'country_en', 'country_kh', 'country_iso3']).agg(
            val_khr=('val_khr', 'sum'),
            val_usd=('val_usd', 'sum'),
            weight_kg=('weight_kg', 'sum')
        ).reset_index()
        country_agg['weight_ton'] = country_agg['weight_kg'] / 1000.0
        country_agg['revenue_share_pct'] = (country_agg['val_usd'] / max(0.001, total_val_usd)) * 100.0
        country_agg['volume_share_pct'] = (country_agg['weight_kg'] / max(0.001, total_weight_kg)) * 100.0
        country_agg['unit_price_usd_per_kg'] = np.where(country_agg['weight_kg'] > 0, country_agg['val_usd'] / country_agg['weight_kg'], 0.0)
        country_agg['share_pct'] = country_agg['revenue_share_pct']
        
        hhi_score = (country_agg['revenue_share_pct'] ** 2).sum()
        country_agg = country_agg.sort_values('val_usd', ascending=False)
        
        # 4. Monthly Seasonality (Temporal Dynamics) & Date Range
        df_clean['yyyy_mm'] = df_clean['year'].astype(str) + '-' + df_clean['month'].astype(str).str.zfill(2)
        monthly_agg = df_clean.groupby('yyyy_mm').agg(
            weight_kton=('weight_kg', lambda x: x.sum()/1000000.0),
            val_million_usd=('val_usd', lambda x: x.sum()/1000000.0),
            val_usd=('val_usd', 'sum'),
            val_khr=('val_khr', 'sum'),
            weight_kg=('weight_kg', 'sum')
        ).reset_index().sort_values('yyyy_mm')
        monthly_agg['weight_ton'] = monthly_agg['weight_kg'] / 1000.0
        monthly_agg['unit_price'] = np.where(monthly_agg['weight_kg'] > 0, monthly_agg['val_usd'] / monthly_agg['weight_kg'], 0.0)
        months_list = monthly_agg['yyyy_mm'].tolist()
        
        def format_ym(ym_str):
            try:
                y, m = ym_str.split('-')
                dt = datetime.date(int(y), int(m), 1)
                return dt.strftime('%b %Y')
            except Exception:
                return ym_str

        if months_list:
            begin_date = format_ym(months_list[0])
            end_date = format_ym(months_list[-1])
        else:
            begin_date = None
            end_date = None

        years_available = sorted(df_clean['year'].dropna().unique().astype(int).tolist()) if 'year' in df_clean.columns else []
        countries_available = sorted(df_clean['country'].dropna().unique().tolist()) if 'country' in df_clean.columns else []
        
        # Multi-dimensional aggregations for interactive cross-chart slicing
        hs4_multi = df_clean.groupby(['hs4_code', 'year', 'country']).agg(
            val_usd=('val_usd', 'sum'),
            val_khr=('val_khr', 'sum'),
            weight_kg=('weight_kg', 'sum')
        ).reset_index()
        hs4_multi['weight_ton'] = hs4_multi['weight_kg'] / 1000.0
        hs4_multi['hs4_official_title'] = hs4_multi['hs4_code'].map(lambda c: get_hs4_official_name(c)[0])
        hs4_multi['hs4_title_en'] = hs4_multi['hs4_code'].map(lambda c: get_hs4_official_name(c)[0])
        hs4_multi['hs4_title_km'] = hs4_multi['hs4_code'].map(lambda c: get_hs4_official_name(c)[1])

        country_multi = df_clean.groupby(['country', 'hs4_code', 'hs8_code', 'year']).agg(
            val_usd=('val_usd', 'sum'),
            val_khr=('val_khr', 'sum'),
            weight_kg=('weight_kg', 'sum')
        ).reset_index()
        country_multi['weight_ton'] = country_multi['weight_kg'] / 1000.0
        cm_cinfo = country_multi['country'].apply(resolve_country)
        country_multi['country_en'] = cm_cinfo.apply(lambda x: x[0])
        country_multi['country_kh'] = cm_cinfo.apply(lambda x: x[1])
        country_multi['country_iso3'] = cm_cinfo.apply(lambda x: x[2])
        country_multi['revenue_share_pct'] = (country_multi['val_usd'] / max(0.001, total_val_usd)) * 100.0
        country_multi['volume_share_pct'] = (country_multi['weight_kg'] / max(0.001, total_weight_kg)) * 100.0
        country_multi['unit_price_usd_per_kg'] = np.where(country_multi['weight_kg'] > 0, country_multi['val_usd'] / country_multi['weight_kg'], 0.0)

        monthly_multi = df_clean.groupby(['yyyy_mm', 'hs4_code', 'hs8_code', 'country', 'year']).agg(
            weight_kton=('weight_kg', lambda x: x.sum()/1000000.0),
            val_million_usd=('val_usd', lambda x: x.sum()/1000000.0),
            val_usd=('val_usd', 'sum'),
            val_khr=('val_khr', 'sum'),
            weight_kg=('weight_kg', 'sum')
        ).reset_index().sort_values('yyyy_mm')
        monthly_multi['weight_ton'] = monthly_multi['weight_kg'] / 1000.0
        
        commodity_multi = df_clean.groupby(['hs4_code', 'hs8_code', 'country', 'year']).agg(
            val_usd=('val_usd', 'sum'),
            val_khr=('val_khr', 'sum'),
            weight_kg=('weight_kg', 'sum')
        ).reset_index()
        commodity_multi['weight_ton'] = commodity_multi['weight_kg'] / 1000.0
        commodity_multi['unit_price_usd_per_kg'] = np.where(commodity_multi['weight_kg'] > 0, commodity_multi['val_usd'] / commodity_multi['weight_kg'], 0.0)
        
        cm_info = commodity_multi['hs8_code'].apply(get_hs8_product_info)
        commodity_multi['name_en'] = cm_info.apply(lambda d: d['name_en'])
        commodity_multi['name_km'] = cm_info.apply(lambda d: d['name_kh'])
        commodity_multi['category_en'] = cm_info.apply(lambda d: d['category_en'])
        commodity_multi['category_km'] = cm_info.apply(lambda d: d['category_kh'])
        commodity_multi['product_name'] = commodity_multi['name_en']
        commodity_multi['revenue_share_pct'] = (commodity_multi['val_usd'] / max(0.001, total_val_usd)) * 100.0
        commodity_multi['volume_share_pct'] = (commodity_multi['weight_ton'] / max(0.001, total_weight_ton)) * 100.0

        # 5. Per-HS8 Commodity Details (for /compare page)
        commodity_details: dict = {}
        for hs8_code, grp in df_clean.groupby('hs8_code'):
            hs8_code_str = clean_hs_code(hs8_code, 8)
            hs4_code_str = clean_hs_code(grp['hs4_code'].iloc[0], 4)
            names = get_product_names_bilingual(hs8_code_str)

            tot_weight_kg  = float(grp['weight_kg'].sum())
            tot_val_usd    = float(grp['val_usd'].sum())
            tot_val_khr    = float(grp['val_khr'].sum())
            avg_price_usd  = tot_val_usd / max(1.0, tot_weight_kg)
            avg_price_khr  = tot_val_khr / max(1.0, tot_weight_kg)
            num_markets    = int(grp['country'].nunique())

            monthly = grp.groupby('yyyy_mm').agg(
                val_usd=('val_usd', 'sum'),
                val_khr=('val_khr', 'sum'),
                weight_kg=('weight_kg', 'sum')
            ).reset_index().sort_values('yyyy_mm')
            monthly['price_usd_per_kg'] = monthly['val_usd'] / monthly['weight_kg'].replace(0, 1)
            monthly['price_khr_per_kg'] = monthly['val_khr'] / monthly['weight_kg'].replace(0, 1)
            monthly_trend = monthly.to_dict(orient='records')

            mkt = grp.groupby('country').agg(
                val_usd=('val_usd', 'sum'),
                val_khr=('val_khr', 'sum'),
                weight_kg=('weight_kg', 'sum')
            ).reset_index()
            mkt['share_pct'] = (mkt['val_usd'] / max(0.001, tot_val_usd)) * 100.0
            mkt = mkt.sort_values('val_usd', ascending=False)
            market_breakdown = mkt.to_dict(orient='records')

            mkt_yearly = grp.groupby(['country', 'year']).agg(
                val_usd=('val_usd', 'sum'),
                val_khr=('val_khr', 'sum'),
                weight_kg=('weight_kg', 'sum')
            ).reset_index()
            yearly_markets = mkt_yearly.to_dict(orient='records')

            raw_vs_processed = None
            pair_info = get_raw_processed_pair(hs4_code_str, hs8_code_str)
            if pair_info:
                partner_hs8 = pair_info['processed_hs8'] if pair_info['is_raw'] else pair_info['raw_hs8']
                partner_grp = df_clean[df_clean['hs8_code'] == partner_hs8]
                partner_weight_kg = float(partner_grp['weight_kg'].sum())
                partner_val_usd   = float(partner_grp['val_usd'].sum())

                raw_hs8      = pair_info['raw_hs8']
                proc_hs8     = pair_info['processed_hs8']
                raw_grp      = df_clean[df_clean['hs8_code'] == raw_hs8]
                proc_grp     = df_clean[df_clean['hs8_code'] == proc_hs8]
                raw_names    = get_product_names_bilingual(raw_hs8)
                proc_names   = get_product_names_bilingual(proc_hs8)

                raw_vs_processed = {
                    'raw_hs8':             raw_hs8,
                    'processed_hs8':       proc_hs8,
                    'raw_name_en':         raw_names['en'],
                    'raw_name_km':         raw_names['km'],
                    'processed_name_en':   proc_names['en'],
                    'processed_name_km':   proc_names['km'],
                    'raw_val_usd':         round(float(raw_grp['val_usd'].sum()), 2),
                    'raw_weight_kg':       round(float(raw_grp['weight_kg'].sum()), 2),
                    'raw_price_usd_per_kg':  round(float(raw_grp['val_usd'].sum()) / max(1, float(raw_grp['weight_kg'].sum())), 4),
                    'raw_price_khr_per_kg':  round(float(raw_grp['val_khr'].sum()) / max(1, float(raw_grp['weight_kg'].sum())), 2),
                    'proc_val_usd':        round(float(proc_grp['val_usd'].sum()), 2),
                    'proc_weight_kg':      round(float(proc_grp['weight_kg'].sum()), 2),
                    'proc_price_usd_per_kg': round(float(proc_grp['val_usd'].sum()) / max(1, float(proc_grp['weight_kg'].sum())), 4),
                    'proc_price_khr_per_kg': round(float(proc_grp['val_khr'].sum()) / max(1, float(proc_grp['weight_kg'].sum())), 2),
                }

            commodity_details[hs8_code_str] = {
                'hs8_code':           hs8_code_str,
                'hs4_code':           hs4_code_str,
                'name_en':            names['en'],
                'name_km':            names['km'],
                'total_val_usd':      round(tot_val_usd, 2),
                'total_val_khr':      round(tot_val_khr, 2),
                'total_weight_kg':    round(tot_weight_kg, 2),
                'total_weight_ton':   round(tot_weight_kg / 1000.0, 4),
                'avg_price_usd_per_kg': round(avg_price_usd, 4),
                'avg_price_khr_per_kg': round(avg_price_khr, 2),
                'num_markets':        num_markets,
                'total_transactions': int(len(grp)),
                'monthly_trend':      monthly_trend,
                'market_breakdown':   market_breakdown,
                'yearly_markets':     yearly_markets,
                'raw_vs_processed':   raw_vs_processed,
            }

        # Flat commodity list for compare-page and overview dropdowns
        commodity_list = [
            {
                'hs8_code':   code,
                'hs4_code':   det['hs4_code'],
                'name_en':    det['name_en'],
                'name_km':    det['name_km'],
                'val_usd':    det['total_val_usd'],
                'weight_kg':  det['total_weight_kg'],
            }
            for code, det in sorted(commodity_details.items())
        ]

        metrics = {
            'begin_date': begin_date,
            'end_date': end_date,
            'available_years': years_available,
            'available_countries': countries_available,
            'total_weight_ton': float(total_weight_ton),
            'total_val_khr': float(total_val_khr),
            'total_val_usd': float(total_val_usd),
            'overall_avg_price_usd_per_kg': float(overall_avg_price_usd_per_kg),
            'hhi_score': float(hhi_score),
            'is_high_risk': bool(hhi_score > 2500),
            'hs8_commodities': hs8_agg.to_dict(orient='records'),
            'hs4_summary': hs4_agg.to_dict(orient='records'),
            'hs8_summary': hs8_agg.to_dict(orient='records'),
            'country_summary': country_agg.to_dict(orient='records'),
            'monthly_summary': monthly_agg.to_dict(orient='records'),
            'hs4_multi': hs4_multi.to_dict(orient='records'),
            'country_multi': country_multi.to_dict(orient='records'),
            'monthly_multi': monthly_multi.to_dict(orient='records'),
            'commodity_multi': commodity_multi.to_dict(orient='records'),
            'commodity_details': commodity_details,
            'commodity_list': commodity_list,
        }
        
        return df_clean, metrics
