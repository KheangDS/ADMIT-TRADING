import os
import json
import re
import hashlib
import time
import requests
from typing import Dict, Any, List, Optional

from app.services.hs_product_service import get_hs4_official_name, clean_hs_code

try:
    from app.config import settings
    DEFAULT_API_KEY = settings.GEMINI_API_KEY
    STORAGE_DIR = os.path.dirname(settings.DB_PATH)
except Exception:
    DEFAULT_API_KEY = ""
    STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")

class AIService:
    def __init__(self):
        self.api_key = DEFAULT_API_KEY or os.getenv("GEMINI_API_KEY", "")
        if not self.api_key:
            self.api_key = self._load_key_from_dotenv()

        # Highly available models on v1beta with fast response times
        self.model_candidates = ["gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.5-flash"]
        self.cache_file = os.path.join(STORAGE_DIR, "ai_insights_cache.json")
        self._cache: Dict[str, Any] = self._load_cache()

    def _load_key_from_dotenv(self) -> str:
        """Helper to find and parse GEMINI_API_KEY from .env files if not in environment."""
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
            os.path.join(os.getcwd(), ".env"),
            os.path.join(os.getcwd(), "backend", ".env")
        ]
        for env_path in possible_paths:
            if os.path.exists(env_path):
                try:
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip().startswith("GEMINI_API_KEY="):
                                return line.split("=", 1)[1].strip().strip('"').strip("'")
                except Exception:
                    pass
        return ""

    def _load_cache(self) -> Dict[str, Any]:
        """Loads cached AI chart insights from persistent JSON storage."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"[AI Service] Note on loading cache: {e}")
        return {}

    def _save_cache(self) -> None:
        """Persists AI chart insights cache to JSON storage."""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[AI Service] Warning saving cache: {e}")

    def _clean_chapter_title(self, cat: Dict[str, Any]) -> str:
        code = clean_hs_code(cat.get("hs4_code", ""), 4)
        t_en, _, _, _ = get_hs4_official_name(code, cat.get("hs4_desc", ""))
        title = cat.get("title_en") or cat.get("official_title") or t_en or f"Chapter {code}"
        return f"{title} (HS {code})"

    def _compute_data_hash(self, metrics: Dict[str, Any]) -> str:
        """Computes a deterministic hash fingerprint representing the dataset content."""
        total_usd = round(float(metrics.get("total_val_usd", 0)), 2)
        total_ton = round(float(metrics.get("total_weight_ton", 0)), 2)
        begin_date = str(metrics.get("begin_date", ""))
        end_date = str(metrics.get("end_date", ""))
        
        hs4_items = sorted(
            [
                (str(c.get("hs4_code")), round(float(c.get("val_usd", 0)), 2), round(float(c.get("weight_ton", c.get("weight_tonnes", 0))), 2))
                for c in metrics.get("hs4_summary", [])
            ],
            key=lambda x: x[0]
        )
        
        top_countries = sorted(
            [
                (str(c.get("country")), round(float(c.get("val_usd", 0)), 2))
                for c in metrics.get("country_summary", [])[:10]
            ],
            key=lambda x: x[0]
        )
        
        fingerprint_data = {
            "total_usd": total_usd,
            "total_ton": total_ton,
            "begin_date": begin_date,
            "end_date": end_date,
            "hs4": hs4_items,
            "countries": top_countries
        }
        
        fingerprint_json = json.dumps(fingerprint_data, sort_keys=True, default=str)
        return hashlib.sha256(fingerprint_json.encode("utf-8")).hexdigest()

    def _call_gemini_api(self, prompt: str, is_json: bool = False) -> Optional[str]:
        """Calls Google Gemini API via REST with automatic fallback through model candidates."""
        if not self.api_key:
            return None

        for model in self.model_candidates:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            payload: Dict[str, Any] = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            if is_json:
                payload["generationConfig"] = {
                    "response_mime_type": "application/json"
                }

            for attempt in range(2):
                try:
                    res = requests.post(url, json=payload, timeout=20)
                    if res.status_code == 200:
                        data = res.json()
                        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip()
                    elif res.status_code == 503:
                        if attempt == 0:
                            time.sleep(0.5)
                            continue
                    else:
                        break
                except Exception:
                    break

        return None

    def generate_chart_meanings_and_strategy(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates chart explanations, key takeaways, and executive strategies using real Gemini LLM.
        Caches results by dataset hash so that unchanged data returns instantly without repeated LLM calls.
        """
        data_hash = self._compute_data_hash(metrics)

        # 1. Check persistent cache
        if data_hash in self._cache:
            cached_data = self._cache[data_hash]
            required_keys = ["commodity_bar_meaning", "country_donut_meaning", "market_share_table_meaning", "seasonality_line_meaning", "executive_strategy"]
            if all(k in cached_data for k in required_keys):
                return cached_data

        # 2. Prepare structured data summary for LLM prompt
        total_usd = metrics.get('total_val_usd', 0)
        total_weight = metrics.get('total_weight_ton', 0)
        avg_price = metrics.get('overall_avg_price_usd_per_kg', 0)
        begin_date = metrics.get('begin_date', 'N/A')
        end_date = metrics.get('end_date', 'N/A')
        hs8_list = metrics.get('hs8_commodities', metrics.get('hs8_summary', metrics.get('hs4_summary', [])))
        country_list = metrics.get('country_summary', [])
        monthly_list = metrics.get('monthly_summary', [])

        # Chart 1 Data: Top HS8 Commodities (Donut Chart)
        hs8_chart_summary = []
        for item in hs8_list[:8]:
            code = item.get('hs8_code') or item.get('hs4_code', '')
            name = item.get('name_en') or item.get('product_name') or f"HS {code}"
            val = item.get('val_usd', 0)
            share_rev = item.get('revenue_share_pct', (val / max(1.0, total_usd)) * 100.0)
            weight = item.get('weight_ton', item.get('weight_tonnes', 0))
            price_kg = item.get('unit_price_usd_per_kg', 0)
            hs8_chart_summary.append(
                f"- {name} (HS {code}): ${val/1e6:.2f}M USD ({share_rev:.1f}% revenue share), {weight:,.1f} Tonnes, Unit Price = ${price_kg:.2f}/kg"
            )

        # Chart 2 Data: Destination Countries Ranking (Horizontal Bar Chart)
        country_chart_summary = []
        for c in country_list[:6]:
            val = c.get('val_usd', 0)
            share = (val / max(1.0, total_usd)) * 100.0
            weight = c.get('weight_ton', c.get('weight_tonnes', 0))
            cname = c.get('country_en') or c.get('country')
            country_chart_summary.append(
                f"- {cname}: ${val/1e6:.2f}M USD ({share:.1f}% revenue share), {weight:,.1f} Tonnes"
            )

        # Chart 3 Data: Top 10 Destination Market Share Table
        table_chart_summary = []
        for idx, c in enumerate(country_list[:10], 1):
            val = c.get('val_usd', 0)
            rev_share = (val / max(1.0, total_usd)) * 100.0
            weight = c.get('weight_ton', c.get('weight_tonnes', 0))
            vol_share = (weight / max(0.001, total_weight)) * 100.0
            cname = c.get('country_en') or c.get('country')
            table_chart_summary.append(
                f"#{idx} {cname}: Volume = {weight:,.1f} Tonnes ({vol_share:.1f}%), Revenue = ${val/1e6:.2f}M USD ({rev_share:.1f}%)"
            )

        # Chart 4 Data: Monthly Export Trajectory Timeline (Line Chart)
        monthly_chart_summary = []
        peak_month = max(monthly_list, key=lambda x: x.get('val_usd', 0)) if monthly_list else {}
        low_month = min(monthly_list, key=lambda x: x.get('val_usd', 0)) if monthly_list else {}
        for m in monthly_list:
            ym = m.get('yyyy_mm', '')
            val = m.get('val_usd', 0)
            weight = m.get('weight_ton', m.get('weight_kg', 0) / 1000.0)
            monthly_chart_summary.append(f"- {ym}: ${val/1e6:.2f}M USD ({weight:,.1f} Tonnes)")

        prompt = f"""
You are a senior agricultural trade intelligence analyst for Cambodia.
Based strictly on the concrete data points of the 4 dashboard charts provided below, generate accurate, professional, executive-level insights for each chart and an overall strategy.

REPORTING PERIOD: {begin_date} to {end_date}
TOTAL EXPORT VALUE: ${total_usd/1e6:.2f} Million USD (${total_usd:,.0f} USD)
TOTAL EXPORT VOLUME: {total_weight:,.1f} Tonnes
AVERAGE UNIT PRICE: ${avg_price:.2f}/kg

=======================================================
[CHART 1] COMMODITIES EXPORT SHARE (DONUT CHART)
Top commodities by export value and volume:
{chr(10).join(hs8_chart_summary)}

=======================================================
[CHART 2] TOP DESTINATION COUNTRIES REVENUE (HORIZONTAL BAR CHART)
Ranking of destination partner countries:
{chr(10).join(country_chart_summary)}

=======================================================
[CHART 3] TOP 10 DESTINATION MARKET SHARE SUMMARY (TABLE)
Top destination markets by volume and value breakdown:
{chr(10).join(table_chart_summary)}

=======================================================
[CHART 4] MONTHLY EXPORT TRAJECTORY (LINE CHART)
Monthly timeline dynamic:
- Peak export month: {peak_month.get('yyyy_mm', 'N/A')} (${peak_month.get('val_usd', 0)/1e6:.2f}M USD, {peak_month.get('weight_ton', 0):,.1f} Tonnes)
- Lowest export month: {low_month.get('yyyy_mm', 'N/A')} (${low_month.get('val_usd', 0)/1e6:.2f}M USD, {low_month.get('weight_ton', 0):,.1f} Tonnes)
Monthly points:
{chr(10).join(monthly_chart_summary)}
=======================================================

Respond ONLY with valid JSON in this exact structure:
{{
  "commodity_bar_meaning": {{
    "explanation": "1 concise sentence explaining what this Donut Chart displays.",
    "key_takeaway": "1 sentence citing exact top commodity names and percentages from Chart 1 data above.",
    "action": "1 actionable recommendation to enhance domestic processing and value addition for dominant crops."
  }},
  "country_donut_meaning": {{
    "explanation": "1 concise sentence explaining what this Horizontal Bar Chart displays.",
    "key_takeaway": "1 sentence summarizing top buyer nations and their revenue shares from Chart 2 data above (do NOT mention HHI).",
    "action": "1 actionable recommendation for export market diversification."
  }},
  "market_share_table_meaning": {{
    "explanation": "1 concise sentence explaining what this Top 10 destination market summary table outlines.",
    "key_takeaway": "1 sentence citing exact table figures from Chart 3 data (e.g. top partner shares).",
    "action": "1 policy recommendation to expand direct market access beyond regional intermediaries."
  }},
  "seasonality_line_meaning": {{
    "explanation": "1 concise sentence explaining what this Monthly Timeline Line Chart tracks.",
    "key_takeaway": "1 sentence citing the peak month and seasonal volume trends from Chart 4 data above.",
    "action": "1 logistics/infrastructure recommendation (e.g. cold storage, warehousing) to stabilize seasonal volatility."
  }},
  "executive_strategy": [
    "Strategic priority 1 (Commodity value-addition)...",
    "Strategic priority 2 (Destination diversification)...",
    "Strategic priority 3 (Post-harvest logistics & cold-chain)..."
  ]
}}

FORMATTING CONSTRAINTS:
1. Ground all numbers strictly in the concrete data points provided above. Do not invent metrics.
2. Always use clean, professional English commodity and country names.
3. For the destination country chart (country_donut_meaning), do NOT mention 'HHI' or 'Herfindahl-Hirschman Index' in key_takeaway; cite partner country shares directly.
4. Output pure JSON without markdown code fences.
"""

        response_text = self._call_gemini_api(prompt, is_json=True)
        if response_text:
            try:
                clean_json = re.sub(r"^```json\s*", "", response_text, flags=re.MULTILINE)
                clean_json = re.sub(r"```$", "", clean_json, flags=re.MULTILINE).strip()
                parsed = json.loads(clean_json)
                
                if "market_share_table_meaning" in parsed and "price_jump_meaning" not in parsed:
                    parsed["price_jump_meaning"] = parsed["market_share_table_meaning"]
                if "price_jump_meaning" in parsed and "market_share_table_meaning" not in parsed:
                    parsed["market_share_table_meaning"] = parsed["price_jump_meaning"]

                required_keys = ["commodity_bar_meaning", "country_donut_meaning", "market_share_table_meaning", "seasonality_line_meaning", "executive_strategy"]
                if all(k in parsed for k in required_keys):
                    self._cache[data_hash] = parsed
                    self._save_cache()
                    return parsed
            except Exception as e:
                print(f"[AI Service] Error parsing Gemini JSON response: {e}")

        # High-Quality Dynamic Fallback (No Hardcoded Numbers, No HHI)
        top_crop = hs8_list[0].get('name_en') if len(hs8_list) > 0 else 'Primary Commodity'
        top_crop_val = hs8_list[0].get('val_usd', 0) if len(hs8_list) > 0 else total_usd
        top_crop_share = (top_crop_val / max(0.001, total_usd)) * 100.0
        
        top1_country = country_list[0].get('country_en', country_list[0].get('country', 'Primary Destination')) if len(country_list) > 0 else 'Primary Destination'
        top1_val = country_list[0].get('val_usd', 0) if len(country_list) > 0 else total_usd
        top1_share = (top1_val / max(0.001, total_usd)) * 100.0
        top2_share = (sum(c.get('val_usd', 0) for c in country_list[:2]) / max(0.001, total_usd)) * 100.0 if len(country_list) > 1 else top1_share

        peak_month_str = peak_month.get('yyyy_mm', 'peak harvest season')
        peak_month_val = peak_month.get('val_usd', 0)

        fallback_insights = {
            'commodity_bar_meaning': {
                'explanation': 'This donut chart displays the export volume and revenue contribution across major 8-digit HS8 agricultural commodities.',
                'key_takeaway': f'{top_crop} serves as the primary export revenue engine, generating {top_crop_share:.1f}% (${top_crop_val/1e6:.2f}M USD) of total agricultural export value.',
                'action': 'Prioritize targeted infrastructure and domestic value addition to maximize processing margins for top-tier commodity crops.'
            },
            'country_donut_meaning': {
                'explanation': 'This horizontal bar chart displays export revenue ranking across international destination partner countries.',
                'key_takeaway': f'{top1_country} leads as the top buyer absorbing {top1_share:.1f}% (${top1_val/1e6:.2f}M USD), with the top two destination partners capturing {top2_share:.1f}% of total trade value.',
                'action': 'Establish direct bilateral trade agreements and cold-chain shipping corridors to diversify into high-value consumer markets.'
            },
            'market_share_table_meaning': {
                'explanation': 'This table summarizes market share across top destination countries by export volume and revenue.',
                'key_takeaway': f'The top two partner markets absorb {top2_share:.1f}% of total exported agricultural volume and revenue.',
                'action': 'Expand direct market linkages with international buyers to capture higher export margins and reduce reliance on border transit hubs.'
            },
            'price_jump_meaning': {
                'explanation': 'This table summarizes market share across top destination countries by export volume and revenue.',
                'key_takeaway': f'The top two partner markets absorb {top2_share:.1f}% of total exported agricultural volume and revenue.',
                'action': 'Expand direct market linkages with international buyers to capture higher export margins and reduce reliance on border transit hubs.'
            },
            'seasonality_line_meaning': {
                'explanation': 'This line chart tracks monthly export trajectory across the trade reporting timeline.',
                'key_takeaway': f'Monthly export value peaked at ${peak_month_val/1e6:.2f}M USD in {peak_month_str}, showing pronounced seasonal harvest dynamics.',
                'action': 'Expand post-harvest cold-storage and warehouse warrant systems to stagger supply and capture premium off-season unit prices.'
            },
            'executive_strategy': [
                f'Accelerate domestic agro-processing capacity for {top_crop} to capture higher processing margins domestically.',
                f'Diversify international trade destinations beyond {top1_country} by securing direct phytosanitary trade protocols with regional and global markets.',
                'Invest in temperature-controlled warehousing and logistical infrastructure to smooth out post-harvest price volatility.'
            ]
        }
        
        self._cache[data_hash] = fallback_insights
        self._save_cache()
        return fallback_insights

    def answer_dataset_question(self, session_id: str, question: str, metrics: Dict[str, Any], duckdb_results: List[Dict[str, Any]]) -> str:
        """Answers user Q&A strictly grounded in the dataset metrics using Gemini LLM with rich dynamic synthesis."""
        rate = metrics.get('exchange_rate_khr_usd', 4000)
        total_usd = metrics.get('total_val_usd', 0)
        if not total_usd and 'total_val_khr' in metrics:
            total_usd = metrics['total_val_khr'] / max(1.0, rate)
            
        total_weight = metrics.get('total_weight_ton', 0)
        if not total_weight and 'total_weight_kg' in metrics:
            total_weight = metrics['total_weight_kg'] / 1000.0
            
        hs8_list = metrics.get('hs8_commodities', metrics.get('hs8_summary', metrics.get('hs4_summary', [])))
        country_list = metrics.get('country_summary', [])
        monthly_list = metrics.get('monthly_summary', [])
        
        q_clean = question.strip().lower()
        if q_clean in ['hi', 'hii', 'hiii', 'hello', 'hey', 'good morning', 'good afternoon', 'greetings']:
            return "Hello! 👋 I'm your AI Agricultural Trade Assistant. I'm ready to help you analyze your trade dataset. What would you like to know?"

        # Identify query intent
        is_chart_inquiry = any(w in q_clean for w in [
            "chart", "visual context:", "explain the key data insights", "donut", "bar chart", 
            "line chart", "market share table", "overview graph"
        ])
        
        is_comparison = any(w in f" {q_clean} " for w in [
            " vs ", " versus ", "compare ", "comparison ", "difference between "
        ])
        
        is_list_request = any(w in q_clean for w in [
            "list", "breakdown", "break down", "show all", "all commodities", "all products", 
            "all countries", "itemized", "table of", "every", "by country", "by month", 
            "by product", "by commodity", "by tariff", "details", "current"
        ])
        
        is_single_metric = any(w in q_clean for w in [
            "total", "volume", "revenue", "value", "worth", "val", "how much", "how many", 
            "amount", "quantity", "sum", "overall", "unit price", "price", "average price", 
            "avg price", "share", "percentage", "pct", "weight", "tonnes", "tons", "kg", 
            "only want", "just want", "only the", "what is the", "tell me the"
        ]) and not is_list_request and not is_chart_inquiry

        # Build focused, noise-free context
        context_parts = []
        
        # 1. Exact DuckDB query result is primary truth
        if duckdb_results:
            context_parts.append(f"EXACT DUCKDB QUERY RESULT:\n{json.dumps(duckdb_results, indent=2, default=str)}")
        
        # 2. Add minimal macro context
        context_parts.append(f"DATASET TOTALS: Total Export Revenue = ${total_usd/1e6:.2f}M USD (${total_usd:,.0f} USD), Total Export Volume = {total_weight:,.2f} Tonnes, Overall Average Price = ${metrics.get('overall_avg_price_usd_per_kg', 0):.2f}/kg")

        # 3. If chart inquiry, provide structured chart components
        if is_chart_inquiry:
            if any(w in q_clean for w in ["commodity", "donut", "share"]):
                context_parts.append(f"TOP COMMODITIES:\n" + "\n".join([
                    f"- {c.get('name_en') or c.get('product_name')}: ${c.get('val_usd',0)/1e6:.2f}M USD, {c.get('weight_ton',0):,.1f} Tonnes, ${c.get('unit_price_usd_per_kg',0):.2f}/kg"
                    for c in hs8_list[:8]
                ]))
            elif any(w in q_clean for w in ["country", "destination", "market", "bar"]):
                context_parts.append(f"TOP BUYER COUNTRIES:\n" + "\n".join([
                    f"- {c.get('country_en') or c.get('country')}: ${c.get('val_usd',0)/1e6:.2f}M USD ({(c.get('val_usd',0)/max(1.0, total_usd))*100:.1f}%), {c.get('weight_ton',0):,.1f} Tonnes"
                    for c in country_list[:8]
                ]))
            elif any(w in q_clean for w in ["month", "timeline", "season", "trend"]):
                context_parts.append(f"MONTHLY TIMELINE:\n" + "\n".join([
                    f"- {m.get('yyyy_mm')}: ${m.get('val_usd',0)/1e6:.2f}M USD, {m.get('weight_ton',0):,.1f} Tonnes"
                    for m in monthly_list
                ]))

        context_summary = "\n\n".join(context_parts)

        # Precise Mode Prompt Instructions
        if is_single_metric:
            rules = """
CRITICAL DIRECT SINGLE-METRIC RULES:
1. Answer ONLY what the user asked for.
2. Provide the direct headline metric in ONE single, concise, authoritative sentence (e.g., "The total export volume of Pepper commodities is 6,017.83 Tonnes.").
3. Do NOT list sub-products, chapters, or itemized breakdowns.
4. Do NOT mention unrelated crops, other chapter products, or unrequested countries.
5. Do NOT include disclaimers, notes, or macroeconomic recommendations.
6. NEVER include persona introductions (DO NOT say "As a Senior Analyst...").
7. Ground your numbers strictly in the exact DuckDB Query Result provided above.
"""
        elif is_comparison:
            rules = """
CRITICAL COMPARISON RULES:
1. Compare ONLY the specific requested entities directly and concisely.
2. Provide a 2-sentence summary comparing Volume (Tonnes), Value ($ USD), and Unit Price ($/kg) for each entity based on the DuckDB query results.
3. NEVER include persona introductions or filler openers.
4. Do NOT mention unrelated commodities or countries.
"""
        elif is_chart_inquiry:
            rules = """
CRITICAL CHART INSIGHT RULES:
1. Explain ONLY the data patterns, numbers, rankings, and visual comparisons shown in that specific chart.
2. Structure chart response clearly:
   ### 1. Chart Summary
   (1-2 clear sentences summarizing what the visual displays)
   ### 2. Key Data Insights
   (Bullet points detailing the specific numbers, shares %, top categories/destinations, comparisons, and rankings shown in the chart)
   ### 3. Notable Observations
   (Key data patterns, seasonal spikes, or specific product differences visible in the graph)
3. Do NOT mention HHI or broad national macroeconomic policy roadmaps.
"""
        elif is_list_request:
            rules = """
CRITICAL LIST / BREAKDOWN RULES:
1. Output a clean, concise bullet list of the commodities from the DuckDB query result.
2. Format each item as: * **Commodity Name** (HS8 code)
3. Jump DIRECTLY into the list with a simple 1-line header (e.g., "The following are the [commodity] commodities available in the dataset:").
4. NEVER include robotic persona preambles like "As a Senior Agricultural Trade Data Analyst...", "I have processed...", or "Based on the records...".
5. If the user asked about a specific crop (e.g., pepper), include ONLY that crop's products. Never include related or adjacent sub-products (e.g. do NOT include chili in pepper).
"""
        else:
            rules = """
CRITICAL DATA ANALYST RULES:
1. Answer directly, concisely, and accurately based strictly on the trade dataset context and DuckDB query results.
2. NEVER include conversational filler, persona introductions, or robotic preambles.
3. Focus strictly on the scope of the user's question without unrequested filler.
"""

        prompt = f"""
{rules}

DATA CONTEXT:
{context_summary}

USER QUESTION: "{question}"

Direct Answer:
"""

        response = self._call_gemini_api(prompt, is_json=False)
        if response:
            # Programmatically clean any accidental persona preambles
            cleaned = re.sub(r'^(?:As a (?:Senior )?Agricultural.*?(?:\.|\:|\n)\s*)+', '', response, flags=re.IGNORECASE).strip()
            cleaned = re.sub(r'^(?:Based on (?:the )?(?:current )?trade records.*?(?:\.|\:|\n)\s*)+', '', cleaned, flags=re.IGNORECASE).strip()
            cleaned = re.sub(r'^(?:I have processed.*?(?:\.|\:|\n)\s*)+', '', cleaned, flags=re.IGNORECASE).strip()
            if cleaned:
                return cleaned
            return response

        # Robust Data-Grounded Fallback (if Gemini API is unreachable)
        if is_single_metric and duckdb_results:
            row = duckdb_results[0]
            raw_scope = str(row.get('scope') or row.get('product_name') or row.get('country') or row.get('hs4_code') or 'agricultural trade')
            if raw_scope.endswith(' Total'):
                scope_display = raw_scope[:-6]
            elif raw_scope in ['Dataset', 'agricultural trade']:
                scope_display = 'agricultural exports'
            else:
                scope_display = raw_scope

            vol = row.get('total_volume_ton', row.get('volume_ton', 0))
            val = row.get('total_val_usd', row.get('val_usd', 0))
            price = row.get('avg_price_usd_per_kg', row.get('price_usd_per_kg', 0))

            if any(w in q_clean for w in ["volume", "ton", "weight", "how much", "how many"]):
                return f"The total export volume of **{scope_display}** is **{vol:,.2f} Tonnes**."
            elif any(w in q_clean for w in ["revenue", "value", "dollar", "$", "worth", "val"]):
                return f"The total export revenue of **{scope_display}** is **${val/1e6:.2f}M USD** (${val:,.2f} USD)."
            elif any(w in q_clean for w in ["price", "unit price", "$/kg", "cost"]):
                return f"The average export unit price of **{scope_display}** is **${price:.2f}/kg**."
            else:
                return f"The total export of **{scope_display}** is **{vol:,.2f} Tonnes** valued at **${val/1e6:.2f}M USD** (average **${price:.2f}/kg**)."

        if is_comparison and len(duckdb_results) >= 2:
            r1, r2 = duckdb_results[0], duckdb_results[1]
            e1 = r1.get('entity') or r1.get('country') or r1.get('product_name') or 'Entity 1'
            e2 = r2.get('entity') or r2.get('country') or r2.get('product_name') or 'Entity 2'
            v1, val1 = r1.get('volume_ton', 0), r1.get('val_usd', 0)
            v2, val2 = r2.get('volume_ton', 0), r2.get('val_usd', 0)
            return (
                f"Comparing exports: **{e1}** accounts for **{v1:,.2f} Tonnes** valued at **${val1/1e6:.2f}M USD**, "
                f"while **{e2}** accounts for **{v2:,.2f} Tonnes** valued at **${val2/1e6:.2f}M USD**."
            )

        if is_list_request and duckdb_results:
            lines = ["The following commodities are available in the dataset:"]
            for r in duckdb_results:
                name = r.get('product_name') or r.get('country') or 'Commodity'
                code = r.get('hs8_code') or r.get('hs4_code')
                if code:
                    lines.append(f"* **{name}** (HS8 {code})")
                else:
                    lines.append(f"* **{name}**")
            return "\n".join(lines)

        if is_chart_inquiry:
            top_crop = hs8_list[0].get('name_en') if len(hs8_list) > 0 else 'Primary Commodity'
            top_crop_val = hs8_list[0].get('val_usd', 0) if len(hs8_list) > 0 else total_usd
            top_crop_share = (top_crop_val / max(0.001, total_usd)) * 100.0
            return (
                f"### 1. Chart Summary\n"
                f"This visual displays the export performance metrics grounded strictly in the active dataset.\n\n"
                f"### 2. Key Data Insights\n"
                f"* **Leading Driver**: **{top_crop}** leads the trade data, capturing **${top_crop_val/1e6:.2f}M USD ({top_crop_share:.1f}% share)**.\n"
                f"* **Dataset Totals**: Across all categories, total trade reaches **${total_usd/1e6:.2f} Million USD** ({total_weight:,.2f} Tonnes).\n\n"
                f"### 3. Notable Observations\n"
                f"* High concentration in leading agricultural categories and top partner corridors."
            )

        return f"Across the active trade dataset, total agricultural export value is **${total_usd/1e6:.2f} Million USD** ({total_weight:,.2f} Tonnes) at an average unit price of **${metrics.get('overall_avg_price_usd_per_kg', 0):.2f}/kg**."

ai_service = AIService()
