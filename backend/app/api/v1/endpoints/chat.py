import re
import difflib
from typing import Dict, Any, List, Optional
from fastapi import APIRouter
from app.models.schemas import ChatRequest, ChatResponse
from app.api.v1.endpoints.upload import SESSION_STORE
from app.services.etl_service import ETLService
from app.services.duckdb_service import duckdb_service
from app.services.ai_service import ai_service
from app.services.exchange_rate_service import exchange_rate_service

router = APIRouter()

MONTH_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12
}

def extract_search_terms(question: str) -> List[str]:
    """Extracts search tokens and bigrams from user prompt, ignoring stop words."""
    STOP_WORDS = {
        "the", "a", "an", "all", "of", "and", "or", "in", "for", "on", "with", "by", "at", "from",
        "to", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
        "did", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "it", "its",
        "list", "show", "give", "tell", "me", "find", "get", "current", "available", "commodity",
        "commodities", "product", "products", "item", "items", "dataset", "data", "trade", "export",
        "exports", "exported", "please", "can", "you", "i", "want", "only", "just", "know", "see",
        "breakdown", "table", "chart", "graph", "overview", "total", "volume", "revenue", "value",
        "price", "unit", "usd", "tonnes", "tons", "ton", "kg", "khr", "amount", "summary", "how",
        "much", "many", "there", "about", "details", "record", "records"
    }
    q_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', question.lower())
    raw_tokens = [t.strip() for t in q_clean.split() if len(t.strip()) >= 2]
    keywords = [t for t in raw_tokens if t not in STOP_WORDS]
    
    # Bigrams (e.g. "cashew nut", "black pepper", "white pepper", "fresh mango")
    bigrams = []
    for i in range(len(raw_tokens) - 1):
        if raw_tokens[i] not in ["the", "a", "an", "of", "in", "to", "for"] and raw_tokens[i+1] not in ["the", "a", "an", "of", "in", "to", "for"]:
            bigrams.append(f"{raw_tokens[i]} {raw_tokens[i+1]}")
            
    return bigrams + keywords

def discover_db_entities(session_id: str, question: str) -> Dict[str, Any]:
    """
    100% Dynamic Database Entity Discovery:
    Discovers matching products, HS codes, and countries directly from the active DuckDB dataset.
    Zero hardcoded dictionaries!
    """
    search_terms = extract_search_terms(question)
    q_low = question.lower()
    
    try:
        distinct_prods = duckdb_service.execute_sql(
            session_id, 
            "SELECT DISTINCT hs8_code, hs4_code, product_name, hs4_desc FROM trade_data"
        )
        distinct_countries = duckdb_service.execute_sql(
            session_id, 
            "SELECT DISTINCT country FROM trade_data WHERE country IS NOT NULL"
        )
    except Exception:
        distinct_prods = []
        distinct_countries = []
        
    db_product_rows = distinct_prods or []
    db_country_names = [c.get('country') for c in (distinct_countries or []) if c.get('country')]
    
    matched_products = []
    matched_countries = []
    
    # Check numeric HS codes in query
    hs8_match = re.search(r'\b(0\d{7}|\d{8})\b', question)
    hs4_match = re.search(r'\b(0\d{3}|\d{4})\b', question)
    
    # Match Countries dynamically from database
    for c_name in db_country_names:
        c_clean = c_name.lower().strip()
        if re.search(rf"\b{re.escape(c_clean)}\b", q_low) or (len(c_clean) >= 4 and c_clean in q_low):
            if c_name not in matched_countries:
                matched_countries.append(c_name)
                
    matched_hs8_codes = set()
    
    # Pass 1: Direct substring match against product_name and hs8_code
    for term in search_terms:
        term_clean = term.lower()
        if len(term_clean) < 3:
            continue
            
        for row in db_product_rows:
            p_name = str(row.get('product_name', '')).lower()
            code8 = str(row.get('hs8_code', ''))
            
            if term_clean in p_name or term_clean == code8:
                # Disambiguation: If searching for 'pepper', don't pull 'chili' / 'capsicum' if query didn't mention chili
                if 'pepper' in term_clean and 'chili' not in q_low and 'chilli' not in q_low and 'capsicum' not in q_low:
                    if 'chili' in p_name or 'chilli' in p_name or 'capsicum' in p_name:
                        continue
                        
                if code8 not in matched_hs8_codes:
                    matched_hs8_codes.add(code8)
                    matched_products.append(row)
                    
    # Pass 2: If no product_name matched, match against hs4_desc
    if not matched_products:
        for term in search_terms:
            term_clean = term.lower()
            if len(term_clean) < 3:
                continue
                
            for row in db_product_rows:
                h_desc = str(row.get('hs4_desc', '')).lower()
                code8 = str(row.get('hs8_code', ''))
                
                if term_clean in h_desc:
                    if code8 not in matched_hs8_codes:
                        matched_hs8_codes.add(code8)
                        matched_products.append(row)

    # Pass 3: Multi-word Fuzzy match against product names if still nothing matched
    if not matched_products and search_terms:
        all_p_words: Dict[str, List[Dict[str, Any]]] = {}
        for row in db_product_rows:
            for word in re.findall(r'[a-zA-Z]{3,}', str(row.get('product_name', '')).lower()):
                all_p_words.setdefault(word, []).append(row)
                
        for term in search_terms:
            close_matches = difflib.get_close_matches(term, all_p_words.keys(), n=2, cutoff=0.75)
            for m in close_matches:
                for row in all_p_words[m]:
                    code8 = str(row.get('hs8_code', ''))
                    p_name = str(row.get('product_name', '')).lower()
                    
                    if 'pep' in term and 'chili' not in q_low and 'chilli' not in q_low and 'capsicum' not in q_low:
                        if 'chili' in p_name or 'chilli' in p_name or 'capsicum' in p_name:
                            continue
                            
                    if code8 not in matched_hs8_codes:
                        matched_hs8_codes.add(code8)
                        matched_products.append(row)

    return {
        "matched_products": matched_products,
        "matched_countries": matched_countries,
        "hs8_code": hs8_match.group(1) if hs8_match else None,
        "hs4_code": hs4_match.group(1) if hs4_match else None,
        "total_db_products": len(db_product_rows),
        "total_db_countries": len(db_country_names)
    }

def find_matched_month(q_lower: str) -> Optional[int]:
    """Identifies target month number if explicitly requested."""
    for m_name, m_num in MONTH_MAP.items():
        if re.search(rf"\b{re.escape(m_name)}\b", q_lower):
            return m_num
    return None

@router.post("/chat", response_model=ChatResponse)
async def chat_with_dataset(payload: ChatRequest):
    session_id = payload.session_id
    question = payload.question
    rate_val = payload.exchange_rate if (payload.exchange_rate and payload.exchange_rate > 0) else exchange_rate_service.get_current_rate_value()
    
    metrics = {}
    if session_id in SESSION_STORE:
        metrics = SESSION_STORE[session_id]['metrics']
    else:
        df_master = duckdb_service.get_master_dataframe()
        if not df_master.empty:
            _, metrics = ETLService.process_trade_data(df_master, exchange_rate=rate_val)
        
    sql_executed = None
    data_points = None
    
    try:
        q_lower = question.lower()
        
        # 1. 100% Dynamic Database Entity Discovery (Zero Hardcoded Dictionaries)
        discovery = discover_db_entities(session_id, question)
        matched_products = discovery["matched_products"]
        matched_countries = discovery["matched_countries"]
        matched_month = find_matched_month(q_lower)
        hs8_code = discovery["hs8_code"]
        hs4_code = discovery["hs4_code"]
        
        # Intent Classification
        is_chart_inquiry = any(w in q_lower for w in [
            "chart", "visual context:", "explain the key data insights", "donut", "bar chart", 
            "line chart", "market share table", "overview graph"
        ])
        
        is_comparison = any(w in f" {q_lower} " for w in [
            " vs ", " versus ", "compare ", "comparison ", "difference between "
        ])
        
        is_list_or_breakdown = any(w in q_lower for w in [
            "list", "breakdown", "break down", "show all", "all commodities", "all products", 
            "all countries", "itemized", "table of", "every", "by country", "by month", 
            "by product", "by commodity", "by tariff", "details", "current"
        ])
        
        is_single_metric = any(w in q_lower for w in [
            "total", "volume", "revenue", "value", "worth", "val", "how much", "how many", 
            "amount", "quantity", "sum", "overall", "unit price", "price", "average price", 
            "avg price", "share", "percentage", "pct", "weight", "tonnes", "tons", "kg", 
            "only want", "just want", "only the", "what is the", "tell me the"
        ]) and not is_list_or_breakdown and not is_chart_inquiry

        # 1. Comparison Intent (e.g. Comparing 2 distinct countries or 2 commodities)
        if is_comparison and len(matched_countries) >= 2:
            c1, c2 = matched_countries[0], matched_countries[1]
            sql_executed = (
                f"SELECT country AS entity, "
                f"ROUND(SUM(weight_kg)/1000, 2) AS volume_ton, "
                f"ROUND(SUM(val_khr)/{rate_val}, 2) AS val_usd, "
                f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS price_usd_per_kg "
                f"FROM trade_data WHERE LOWER(country) IN ('{c1.lower()}', '{c2.lower()}') "
                f"GROUP BY country"
            )
        elif is_comparison and len(matched_products) >= 2:
            codes_list = [f"'{p['hs8_code']}'" for p in matched_products[:4] if p.get('hs8_code')]
            in_clause = ", ".join(codes_list)
            sql_executed = (
                f"SELECT product_name AS entity, "
                f"ROUND(SUM(weight_kg)/1000, 2) AS volume_ton, "
                f"ROUND(SUM(val_khr)/{rate_val}, 2) AS val_usd, "
                f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS price_usd_per_kg "
                f"FROM trade_data WHERE hs8_code IN ({in_clause}) "
                f"GROUP BY product_name ORDER BY val_usd DESC"
            )
        # 2. Specific Commodity Matched Dynamically in Database
        elif matched_products and not (is_list_or_breakdown and len(matched_products) > 10):
            codes_list = [f"'{p['hs8_code']}'" for p in matched_products if p.get('hs8_code')]
            in_clause = ", ".join(codes_list) if codes_list else "''"
            
            sample_name = matched_products[0].get('product_name', 'Commodity')
            scope_label = sample_name.split(':')[0].split(',')[0].strip() if len(matched_products) > 1 else sample_name
            
            if is_single_metric:
                sql_executed = (
                    f"SELECT '{scope_label}' AS scope, "
                    f"ROUND(SUM(weight_kg)/1000, 2) AS total_volume_ton, "
                    f"ROUND(SUM(val_khr)/{rate_val}, 2) AS total_val_usd, "
                    f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS avg_price_usd_per_kg "
                    f"FROM trade_data WHERE hs8_code IN ({in_clause})"
                )
            else:
                sql_executed = (
                    f"SELECT hs8_code, hs4_code, product_name, "
                    f"ROUND(SUM(weight_kg)/1000, 2) AS volume_ton, "
                    f"ROUND(SUM(val_khr)/{rate_val}, 2) AS val_usd, "
                    f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS price_usd_per_kg "
                    f"FROM trade_data WHERE hs8_code IN ({in_clause}) "
                    f"GROUP BY hs8_code, hs4_code, product_name ORDER BY val_usd DESC"
                )
        # 3. Specific Destination Country Matched Dynamically in Database
        elif matched_countries:
            c_target = matched_countries[0]
            if is_single_metric:
                sql_executed = (
                    f"SELECT country, "
                    f"ROUND(SUM(weight_kg)/1000, 2) AS total_volume_ton, "
                    f"ROUND(SUM(val_khr)/{rate_val}, 2) AS total_val_usd, "
                    f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS avg_price_usd_per_kg "
                    f"FROM trade_data WHERE LOWER(country) = '{c_target.lower()}' "
                    f"GROUP BY country"
                )
            else:
                sql_executed = (
                    f"SELECT hs8_code, product_name, country, "
                    f"ROUND(SUM(weight_kg)/1000, 2) AS volume_ton, "
                    f"ROUND(SUM(val_khr)/{rate_val}, 2) AS val_usd, "
                    f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS price_usd_per_kg "
                    f"FROM trade_data WHERE LOWER(country) = '{c_target.lower()}' "
                    f"GROUP BY hs8_code, product_name, country ORDER BY val_usd DESC"
                )
        # 4. Specific 8-digit HS code query
        elif hs8_code:
            if is_single_metric:
                sql_executed = (
                    f"SELECT hs8_code, product_name, "
                    f"ROUND(SUM(weight_kg)/1000, 2) AS total_volume_ton, "
                    f"ROUND(SUM(val_khr)/{rate_val}, 2) AS total_val_usd, "
                    f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS avg_price_usd_per_kg "
                    f"FROM trade_data WHERE hs8_code = '{hs8_code}' "
                    f"GROUP BY hs8_code, product_name"
                )
            else:
                sql_executed = (
                    f"SELECT hs8_code, hs4_code, product_name, country, year, "
                    f"ROUND(SUM(weight_kg)/1000, 2) AS volume_ton, "
                    f"ROUND(SUM(val_khr)/{rate_val}, 2) AS val_usd, "
                    f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS price_usd_per_kg "
                    f"FROM trade_data WHERE hs8_code = '{hs8_code}' "
                    f"GROUP BY hs8_code, hs4_code, product_name, country, year ORDER BY val_usd DESC"
                )
        # 5. Specific 4-digit HS chapter query
        elif hs4_code:
            if is_single_metric:
                sql_executed = (
                    f"SELECT '{hs4_code}' AS hs4_code, "
                    f"ROUND(SUM(weight_kg)/1000, 2) AS total_volume_ton, "
                    f"ROUND(SUM(val_khr)/{rate_val}, 2) AS total_val_usd, "
                    f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS avg_price_usd_per_kg "
                    f"FROM trade_data WHERE hs4_code = '{hs4_code}'"
                )
            else:
                sql_executed = (
                    f"SELECT hs8_code, hs4_code, product_name, "
                    f"ROUND(SUM(weight_kg)/1000, 2) AS volume_ton, "
                    f"ROUND(SUM(val_khr)/{rate_val}, 2) AS val_usd, "
                    f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS price_usd_per_kg "
                    f"FROM trade_data WHERE hs4_code = '{hs4_code}' "
                    f"GROUP BY hs8_code, hs4_code, product_name ORDER BY val_usd DESC"
                )
        # 6. Specific Month Query (e.g. "Exports in March")
        elif matched_month is not None:
            sql_executed = (
                f"SELECT CAST(year AS VARCHAR) || '-' || LPAD(CAST(month AS VARCHAR), 2, '0') AS yyyy_mm, "
                f"ROUND(SUM(val_khr)/{rate_val}, 2) AS val_usd, "
                f"ROUND(SUM(weight_kg)/1000, 2) AS volume_ton, "
                f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS price_usd_per_kg "
                f"FROM trade_data WHERE month = {matched_month} "
                f"GROUP BY 1 ORDER BY 1 ASC"
            )
        # 7. Seasonality / Monthly Timeline / Peak Month queries
        elif any(w in q_lower for w in ["season", "month", "timeline", "trend", "timing", "harvest", "peak", "highest month", "lowest month", "q1", "q2", "q3", "q4"]):
            if any(w in q_lower for w in ["peak", "highest month", "top month", "max month"]):
                sql_executed = (
                    f"SELECT CAST(year AS VARCHAR) || '-' || LPAD(CAST(month AS VARCHAR), 2, '0') AS yyyy_mm, "
                    f"ROUND(SUM(val_khr)/{rate_val}, 2) AS val_usd, "
                    f"ROUND(SUM(weight_kg)/1000, 2) AS volume_ton, "
                    f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS price_usd_per_kg "
                    f"FROM trade_data GROUP BY 1 ORDER BY val_usd DESC LIMIT 1"
                )
            elif any(w in q_lower for w in ["lowest month", "trough", "minimum month"]):
                sql_executed = (
                    f"SELECT CAST(year AS VARCHAR) || '-' || LPAD(CAST(month AS VARCHAR), 2, '0') AS yyyy_mm, "
                    f"ROUND(SUM(val_khr)/{rate_val}, 2) AS val_usd, "
                    f"ROUND(SUM(weight_kg)/1000, 2) AS volume_ton, "
                    f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS price_usd_per_kg "
                    f"FROM trade_data GROUP BY 1 ORDER BY val_usd ASC LIMIT 1"
                )
            else:
                sql_executed = (
                    f"SELECT CAST(year AS VARCHAR) || '-' || LPAD(CAST(month AS VARCHAR), 2, '0') AS yyyy_mm, "
                    f"ROUND(SUM(val_khr)/{rate_val}, 2) AS val_usd, "
                    f"ROUND(SUM(weight_kg)/1000, 2) AS volume_ton, "
                    f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS price_usd_per_kg "
                    f"FROM trade_data GROUP BY 1 ORDER BY 1 ASC"
                )
        # 8. Destination Countries / Markets / Partners (General or Rankings)
        elif any(w in q_lower for w in ["country", "destination", "market", "buyer", "concentration", "partner"]):
            top_match = re.search(r'\btop\s*(\d+)\b', q_lower)
            limit_n = int(top_match.group(1)) if top_match else (5 if "top" in q_lower else 25)
            sql_executed = (
                f"SELECT country, "
                f"ROUND(SUM(val_khr)/{rate_val}, 2) AS val_usd, "
                f"ROUND(SUM(weight_kg)/1000, 2) AS volume_ton, "
                f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS price_usd_per_kg "
                f"FROM trade_data GROUP BY country ORDER BY val_usd DESC LIMIT {limit_n}"
            )
        # 9. Price / Unit Price / Expensive / Cheapest queries
        elif any(w in q_lower for w in ["unit price", "price/kg", "$/kg", "expensive", "cheapest", "cost per kg", "highest price", "lowest price"]):
            if "cheapest" in q_lower or "lowest price" in q_lower:
                sql_executed = (
                    f"SELECT hs8_code, hs4_code, product_name, "
                    f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS price_usd_per_kg, "
                    f"ROUND(SUM(val_khr)/{rate_val}, 2) AS val_usd, "
                    f"ROUND(SUM(weight_kg)/1000, 2) AS volume_ton "
                    f"FROM trade_data GROUP BY hs8_code, hs4_code, product_name "
                    f"HAVING SUM(weight_kg) > 0 ORDER BY price_usd_per_kg ASC LIMIT 10"
                )
            else:
                sql_executed = (
                    f"SELECT hs8_code, hs4_code, product_name, "
                    f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS price_usd_per_kg, "
                    f"ROUND(SUM(val_khr)/{rate_val}, 2) AS val_usd, "
                    f"ROUND(SUM(weight_kg)/1000, 2) AS volume_ton "
                    f"FROM trade_data GROUP BY hs8_code, hs4_code, product_name ORDER BY price_usd_per_kg DESC LIMIT 10"
                )
        # 10. Global Total / Aggregate (e.g. "What is the total export revenue?")
        elif is_single_metric:
            sql_executed = (
                f"SELECT ROUND(SUM(weight_kg)/1000, 2) AS total_volume_ton, "
                f"ROUND(SUM(val_khr)/{rate_val}, 2) AS total_val_usd, "
                f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS avg_price_usd_per_kg "
                f"FROM trade_data"
            )
        # 11. Commodities / Products / HS8 / List All queries
        elif any(w in q_lower for w in ["commodity", "commodities", "hs8", "product", "products", "item", "items", "crop", "crops", "list", "all"]):
            sql_executed = (
                f"SELECT hs8_code, hs4_code, product_name, "
                f"ROUND(SUM(weight_kg)/1000, 2) AS volume_ton, "
                f"ROUND(SUM(val_khr)/{rate_val}, 2) AS val_usd, "
                f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS price_usd_per_kg "
                f"FROM trade_data GROUP BY hs8_code, hs4_code, product_name ORDER BY val_usd DESC"
            )
        # 12. Dynamic Fallback Overview from DuckDB
        else:
            sql_executed = (
                f"SELECT hs8_code, hs4_code, product_name, "
                f"ROUND(SUM(weight_kg)/1000, 2) AS volume_ton, "
                f"ROUND(SUM(val_khr)/{rate_val}, 2) AS val_usd, "
                f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS price_usd_per_kg "
                f"FROM trade_data GROUP BY hs8_code, hs4_code, product_name ORDER BY val_usd DESC LIMIT 25"
            )
            
        data_points = duckdb_service.execute_sql(session_id, sql_executed)
    except Exception as e:
        print("DuckDB Chat Query Error:", e)
        
    answer = ai_service.answer_dataset_question(session_id, question, metrics, data_points or [])
    
    return ChatResponse(
        question=question,
        answer=answer,
        sql_executed=sql_executed,
        data_points=data_points[:10] if data_points else None
    )
