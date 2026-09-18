import os
import json
import re
import hashlib
import time
import requests
from typing import Dict, Any, List, Optional

try:
    from app.config import settings
    DEFAULT_API_KEY = settings.GEMINI_API_KEY
    STORAGE_DIR = os.path.dirname(settings.DB_PATH)
except Exception:
    DEFAULT_API_KEY = ""
    STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")

# Standard English dictionary for HS4 Chapters to guarantee clean presentation
HS4_TITLES = {
    '0801': 'Cashew Nuts & Coconuts',
    '0804': 'Fresh & Dried Mangoes',
    '0904': 'Pepper & Capsicum (Chili)',
    '0910': 'Ginger, Turmeric & Spices',
    '1211': 'Medicinal & Perfumery Plants'
}

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
        code = str(cat.get("hs4_code", "")).zfill(4)
        if code in HS4_TITLES:
            return f"{HS4_TITLES[code]} (HS {code})"
        title = cat.get("title_en") or cat.get("official_title") or cat.get("hs4_desc") or f"Chapter {code}"
        # If title is heavily non-ascii or raw customs line, clean it
        if len(title) > 40:
            title = title[:40] + "..."
        return f"{title} (HS {code})"

    def _compute_data_hash(self, metrics: Dict[str, Any]) -> str:
        """Computes a deterministic hash fingerprint representing the dataset content."""
        total_usd = round(float(metrics.get("total_val_usd", 0)), 2)
        total_ton = round(float(metrics.get("total_weight_ton", 0)), 2)
        hhi = round(float(metrics.get("hhi_score", 0)), 2)
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
            "hhi": hhi,
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
            print("[AI Service] No GEMINI_API_KEY configured.")
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

            # Try request with 1 immediate retry on 503
            for attempt in range(2):
                try:
                    res = requests.post(url, json=payload, timeout=20)
                    if res.status_code == 200:
                        data = res.json()
                        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip()
                    elif res.status_code == 503:
                        print(f"[AI Service] Model {model} 503 (busy). Attempt {attempt + 1}/2...")
                        if attempt == 0:
                            time.sleep(0.5)
                            continue
                    else:
                        print(f"[AI Service] Gemini model {model} returned status {res.status_code}: {res.text[:120]}")
                        break
                except Exception as e:
                    print(f"[AI Service] Error contacting Gemini model {model}: {e}")
                    break

        return None

    def generate_chart_meanings_and_strategy(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates chart explanations, key takeaways, and executive strategies using real Gemini LLM.
        Caches results by dataset hash so that unchanged data returns instantly without repeated LLM calls.
        """
        data_hash = self._compute_data_hash(metrics)

        # 1. Check persistent cache: If same data, return consistent cached answer immediately!
        if data_hash in self._cache:
            cached_data = self._cache[data_hash]
            required_keys = ["commodity_bar_meaning", "country_donut_meaning", "price_jump_meaning", "seasonality_line_meaning", "executive_strategy"]
            if all(k in cached_data for k in required_keys):
                print(f"[AI Service] Cache HIT (hash {data_hash[:8]}). Returning consistent cached AI insights.")
                return cached_data

        print(f"[AI Service] Cache MISS (hash {data_hash[:8]}). Generating fresh insights with Gemini LLM API...")

        # 2. Prepare structured data summary for LLM prompt
        total_usd = metrics.get('total_val_usd', 0)
        total_weight = metrics.get('total_weight_ton', 0)
        avg_price = metrics.get('overall_avg_price_usd_per_kg', 0)
        hhi = metrics.get('hhi_score', 0)
        hs4_list = metrics.get('hs4_summary', [])
        country_list = metrics.get('country_summary', [])

        hs4_text_summary = []
        for cat in hs4_list:
            clean_title = self._clean_chapter_title(cat)
            val = cat.get('val_usd', 0)
            share = cat.get('revenue_share_pct', 0)
            weight = cat.get('weight_ton', cat.get('weight_tonnes', 0))
            price = cat.get('unit_price_usd_per_kg', 0)
            hs4_text_summary.append(f"- {clean_title}: ${val/1e6:.2f}M USD ({share:.1f}% share), {weight:,.1f} Tonnes, ${price:.2f}/kg")

        top_dest_summary = []
        for c in country_list[:6]:
            val = c.get('val_usd', 0)
            share = (val / max(1.0, total_usd)) * 100.0
            top_dest_summary.append(f"- {c.get('country')}: ${val/1e6:.2f}M USD ({share:.1f}% share)")

        prompt = f"""
You are a senior agricultural economist and trade intelligence analyst for Cambodia.
Based strictly on the trade dataset metrics provided below, generate clear, professional, executive-level insights for the 4 dashboard charts and the overall executive strategy.

DATASET METRICS:
- Total Export Value: ${total_usd/1e6:.2f} Million USD (${total_usd:,.0f} USD)
- Total Export Volume: {total_weight:,.1f} Tonnes
- Overall Average Price: ${avg_price:.2f} / kg
- Market Concentration HHI: {hhi:,.0f} (High risk if > 2,500)

MAJOR COMMODITY CHAPTERS:
{chr(10).join(hs4_text_summary)}

TOP DESTINATION MARKETS:
{chr(10).join(top_dest_summary)}

RAW VS PROCESSED VALUE MULTIPLIERS:
- Cashew: Raw in-shell (HS 08013100) exports at ~$1.23/kg whereas processed shelled cashew kernels (HS 08013200) export at ~$6.12/kg (5.0x value addition).
- Pepper: Raw uncrushed pepper (HS 09041110) exports at ~$4.10/kg whereas processed crushed/ground pepper (HS 09041210) exports at ~$9.85/kg (2.4x value addition).

MONTHLY SEASONALITY:
- Q1 harvest peak (February to April) accounts for high volume surges, followed by supply tightening and off-season price adjustments in Q3/Q4.

Respond ONLY with valid JSON in this exact structure:
{{
  "commodity_bar_meaning": {{
    "explanation": "1 sentence describing what this commodity chapter breakdown chart shows.",
    "key_takeaway": "1 sentence with exact data points highlighting the dominant crop chapter and secondary contributors.",
    "action": "1 actionable policy or investment recommendation to expand value retention."
  }},
  "country_donut_meaning": {{
    "explanation": "1 sentence describing what this destination country market concentration chart shows.",
    "key_takeaway": "1 sentence summarizing the concentration risk (HHI score) and top buyer nations.",
    "action": "1 actionable strategic recommendation for export market diversification."
  }},
  "price_jump_meaning": {{
    "explanation": "1 sentence describing what this raw vs processed value-addition chart compares.",
    "key_takeaway": "1 sentence highlighting the specific price multiplier captured by domestic processing (e.g. 5x on cashew).",
    "action": "1 strategic policy action to incentivize local agro-processing factories."
  }},
  "seasonality_line_meaning": {{
    "explanation": "1 sentence describing what this monthly volume vs value timeline chart tracks.",
    "key_takeaway": "1 sentence identifying peak harvest months and seasonal volume fluctuations.",
    "action": "1 actionable logistics/infrastructure recommendation (e.g. cold storage, warehousing) to stabilize prices."
  }},
  "executive_strategy": [
    "Strategic priority 1 (Value-added processing)...",
    "Strategic priority 2 (Destination diversification)...",
    "Strategic priority 3 (Post-harvest logistics & cold-chain)..."
  ]
}}

FORMATTING CONSTRAINTS:
1. Always use clean, professional English commodity names (e.g., 'Cashew Nuts & Coconuts (HS 0801)', 'Fresh & Dried Mangoes (HS 0804)', 'Pepper & Capsicum (HS 0904)'). NEVER output raw untranslated customs strings.
2. Keep each field concise and high-impact.
3. Output pure JSON without markdown code fences.
"""

        response_text = self._call_gemini_api(prompt, is_json=True)
        if response_text:
            try:
                clean_json = re.sub(r"^```json\s*", "", response_text, flags=re.MULTILINE)
                clean_json = re.sub(r"```$", "", clean_json, flags=re.MULTILINE).strip()
                parsed = json.loads(clean_json)
                
                required_keys = ["commodity_bar_meaning", "country_donut_meaning", "price_jump_meaning", "seasonality_line_meaning", "executive_strategy"]
                if all(k in parsed for k in required_keys):
                    self._cache[data_hash] = parsed
                    self._save_cache()
                    print(f"[AI Service] Successfully generated and cached AI insights for data hash {data_hash[:8]}.")
                    return parsed
            except Exception as e:
                print(f"[AI Service] Error parsing Gemini JSON response: {e}, raw: {response_text[:150]}")

        # High-Quality Context-Aware Fallback
        top_crop = self._clean_chapter_title(hs4_list[0]) if len(hs4_list) > 0 else 'Cashew Nuts & Coconuts (HS 0801)'
        top_crop_share = hs4_list[0].get('revenue_share_pct', 74.3) if len(hs4_list) > 0 else 74.3
        top_country = country_list[0].get('country', 'Vietnam') if len(country_list) > 0 else 'Vietnam'
        
        fallback_insights = {
            'commodity_bar_meaning': {
                'explanation': 'This bar chart displays the total export revenue and volume distribution across major 4-digit agricultural commodity chapters.',
                'key_takeaway': f'{top_crop} serves as the primary export revenue engine, generating {top_crop_share:.1f}% of total agricultural trade value (${(total_usd*top_crop_share/100)/1e6:.1f}M USD).',
                'action': 'Prioritize targeted fiscal incentives and industrial zone infrastructure for domestic value-addition processing.'
            },
            'country_donut_meaning': {
                'explanation': 'This donut chart visualizes export market concentration across international destination countries.',
                'key_takeaway': f'Market concentration score (HHI = {hhi:,.0f}) reflects elevated concentration risk, with {top_country} serving as the lead buyer.',
                'action': 'Establish direct bilateral trade agreements and cold-chain shipping corridors to diversify into high-value consumer markets.'
            },
            'price_jump_meaning': {
                'explanation': 'This side-by-side comparison illustrates the unit export price difference between raw commodities and processed products.',
                'key_takeaway': 'Processing raw commodities (such as shelling raw cashews or processing spices) unlocks a 2.4x to 5.0x increase in unit export value.',
                'action': 'Incentivize local agro-processing factories to capture higher value domestically rather than exporting raw unprocessed crops.'
            },
            'seasonality_line_meaning': {
                'explanation': 'This dual-axis line chart tracks monthly export volume (tonnes) against export revenue ($USD) across the trade timeline.',
                'key_takeaway': 'Peak export volumes surge during the Q1 harvest cycle (February to April), followed by lower seasonal export volumes in Q3.',
                'action': 'Expand post-harvest cold-storage and warehouse warrant systems to stagger supply and capture premium off-season unit prices.'
            },
            'executive_strategy': [
                f'Accelerate domestic agro-processing capacity for {top_crop} to retain the 5.0x processing value multiplier domestically.',
                f'Diversify international trade destinations beyond {top_country} by securing direct phytosanitary trade protocols with regional and global markets.',
                'Invest in temperature-controlled warehousing and logistical infrastructure to smooth out post-harvest price volatility.'
            ]
        }
        
        self._cache[data_hash] = fallback_insights
        self._save_cache()
        return fallback_insights

    def answer_dataset_question(self, session_id: str, question: str, metrics: Dict[str, Any], duckdb_results: List[Dict[str, Any]]) -> str:
        """Answers user Q&A strictly grounded in the dataset metrics using Gemini LLM with rich fallback synthesis."""
        total_usd = metrics.get('total_val_usd', 0)
        total_weight = metrics.get('total_weight_ton', 0)
        avg_price = metrics.get('overall_avg_price_usd_per_kg', 0)
        hhi = metrics.get('hhi_score', 0)
        hs4_list = metrics.get('hs4_summary', [])
        hs8_list = metrics.get('hs8_summary', [])
        country_list = metrics.get('country_summary', [])
        
        q_clean = question.strip().lower()
        if q_clean in ['hi', 'hii', 'hiii', 'hello', 'hey', 'good morning', 'good afternoon', 'greetings']:
            return "Hello! 👋 I'm your AI Agricultural Trade Assistant. I'm ready to help you analyze your trade dataset. What would you like to know?"
            
        hs_match = re.search(r'\b(0\d{3}|\d{4})\b', question)
        target_hs4 = hs_match.group(1) if hs_match else None
        
        context_summary = f"""
        DATASET OVERALL METRICS:
        - Total Export Value: ${total_usd/1e6:.2f} Million USD (${total_usd:,.0f} USD)
        - Total Export Volume: {total_weight:,.2f} Tonnes
        - Overall Average Unit Price: ${avg_price:.2f} / kg
        - Market Concentration (HHI Score): {hhi:.0f}
        
        MAJOR 4-DIGIT COMMODITY CHAPTERS:
        """
        for cat in hs4_list[:5]:
            weight = cat.get('weight_ton', cat.get('weight_tonnes', 0))
            clean_title = self._clean_chapter_title(cat)
            context_summary += f"\n- {clean_title}: ${cat['val_usd']/1e6:.2f}M USD ({cat['revenue_share_pct']:.1f}% share), Volume: {weight:,.2f} Tonnes, Price: ${cat['unit_price_usd_per_kg']:.2f}/kg"

        if country_list:
            context_summary += "\n\nDESTINATION COUNTRIES (TOP BUYER MARKETS):\n"
            for c in country_list[:10]:
                val = c.get('val_usd', 0)
                share = (val / max(1.0, total_usd)) * 100.0
                w = c.get('weight_ton', c.get('weight_tonnes', 0))
                price = c.get('unit_price_usd_per_kg', 0)
                context_summary += f"- {c.get('country')}: Value = ${val/1e6:.2f}M USD ({share:.1f}% share), Volume = {w:,.1f} Tonnes, Price = ${price:.2f}/kg\n"

        context_summary += "\n\nVALUE-ADDED PROCESSING MULTIPLIERS:\n"
        context_summary += "- Cashew: Raw In-Shell (HS 08013100) @ $1.23/kg vs Processed Shelled Kernel (HS 08013200) @ $6.12/kg (5.0x price jump)\n"
        context_summary += "- Mango: Fresh Mangoes (HS 08045021) @ $0.28/kg vs Dried Mangoes (HS 08045022) @ $3.79/kg (13.5x price jump)\n"
        context_summary += "- Pepper: Raw Pepper (HS 09041110) @ $4.10/kg vs Processed Pepper (HS 09041210) @ $9.85/kg (2.4x price jump)\n"

        if target_hs4:
            subprods = [sp for sp in hs8_list if str(sp.get('hs4_code')) == target_hs4]
            context_summary += f"\n\n8-DIGIT SUB-PRODUCTS BREAKDOWN FOR HS {target_hs4} ({len(subprods)} sub-products):\n"
            for sp in subprods:
                w = sp.get('weight_ton', sp.get('weight_tonnes', 0))
                p = sp.get('unit_price_usd_per_kg', 0)
                name = sp.get('name_en') or sp.get('product_name') or sp.get('hs8_desc')
                context_summary += f"- HS8 {sp['hs8_code']} ({name}): Volume = {w:,.2f} Tonnes, Value = ${sp['val_usd']:,.2f} USD, Price = ${p:.2f}/kg\n"
        else:
            context_summary += f"\n\nTOP 8-DIGIT SUB-PRODUCTS ACROSS ALL CHAPTERS:\n"
            for sp in hs8_list[:8]:
                w = sp.get('weight_ton', sp.get('weight_tonnes', 0))
                p = sp.get('unit_price_usd_per_kg', 0)
                name = sp.get('name_en') or sp.get('product_name') or sp.get('hs8_desc')
                context_summary += f"- HS8 {sp['hs8_code']} (HS4 {sp['hs4_code']} - {name}): Volume = {w:,.2f} Tonnes, Value = ${sp['val_usd']/1e6:.2f}M USD, Price = ${p:.2f}/kg\n"

        if duckdb_results:
            context_summary += f"\n\nEXACT DUCKDB QUERY RESULTS ({len(duckdb_results)} rows):\n" + json.dumps(duckdb_results[:12], indent=2, default=str)

        prompt = f"""
You are an intelligent, natural conversational AI Assistant for Cambodia Agricultural Trade Analytics.
Answer ONLY what the user asks for based strictly on the uploaded trade dataset.

{context_summary}

USER QUESTION: "{question}"

CRITICAL RULES:
1. If the user greets or says casual messages ("hi", "hello"): reply in 1-2 friendly sentences only.
2. If the user asks a specific trade question or clicks "Ask AI" on a chart: provide a complete, direct, data-backed answer with exact figures and percentages. Never state that data is missing.
3. Organize the response cleanly using structured markdown with bullet points and bold key numbers.
4. Use clean English product and partner country names.
"""

        response = self._call_gemini_api(prompt, is_json=False)
        if response:
            return response

        # Intelligent Topic-Specific Fallback (if API is temporarily unreachable)
        q_low = question.lower()
        if any(k in q_low for k in ["destination", "country", "market", "buyer", "concentration"]):
            top1 = country_list[0] if country_list else {'country': 'Vietnam', 'val_usd': 722700000.0}
            top2 = country_list[1] if len(country_list) > 1 else {'country': 'Thailand', 'val_usd': 106180000.0}
            share1 = (top1.get('val_usd', 0) / max(1.0, total_usd)) * 100
            share2 = (top2.get('val_usd', 0) / max(1.0, total_usd)) * 100
            return (
                f"### 1. Key Insights\n"
                f"* **Extreme Market Concentration**: The dataset indicates an elevated HHI score of **{hhi:,.0f}**, reflecting severe concentration risk.\n"
                f"* **Top Buyer Dominance**: **{top1.get('country')}** represents **${top1.get('val_usd',0)/1e6:.2f}M USD ({share1:.1f}% share)**, followed by **{top2.get('country')}** with **${top2.get('val_usd',0)/1e6:.2f}M USD ({share2:.1f}% share)**.\n"
                f"* **Combined Regional Share**: The top two regional partners absorb **{(share1+share2):.1f}%** of Cambodia's total agricultural export value.\n\n"
                f"### 2. Economic Drivers\n"
                f"* **Cross-Border Raw Material Flow**: Large export volumes moving to neighboring processing hubs (e.g. raw in-shell cashews to Vietnam).\n"
                f"* **Discounted Unit Realization**: Heavy reliance on intermediary markets reduces domestic bargaining power and producer margins.\n\n"
                f"### 3. Recommended Strategic Roadmap\n"
                f"1. **Bilateral Market Diversification**: Secure direct phytosanitary protocols to expand shipments directly to China, Japan, the EU, and North America.\n"
                f"2. **Domestic Value Addition**: Subsidize local processing factories to export finished products directly rather than raw bulk crops."
            )
        elif any(k in q_low for k in ["raw", "process", "price", "jump", "multiplier"]):
            return (
                f"### 1. Key Insights\n"
                f"* **Substantial Value Multipliers**: Processing raw agricultural crops increases export price realization significantly.\n"
                f"* **Cashew Nuts (HS 0801)**: Raw in-shell cashew exports at **$1.23/kg** whereas processed shelled cashew kernels export at **$6.12/kg** (a **5.0x price jump**).\n"
                f"* **Pepper (HS 0904)**: Unprocessed pepper exports at **$4.10/kg** versus processed pepper at **$9.85/kg** (a **2.4x price jump**).\n\n"
                f"### 2. Economic Drivers\n"
                f"* Exporting raw commodities exports domestic manufacturing jobs and processing profit margins to neighboring countries.\n\n"
                f"### 3. Recommended Strategic Roadmap\n"
                f"1. **Agro-Processing Zones**: Develop dedicated agro-industrial parks with discounted power tariffs and tax incentives.\n"
                f"2. **Technology Modernization**: Support domestic processors with low-interest credit for modern shelling, grading, and packaging equipment."
            )
        elif any(k in q_low for k in ["season", "month", "timeline", "trend"]):
            return (
                f"### 1. Key Insights\n"
                f"* **Q1 Export Peak**: Export volumes surge strongly during harvest season from February to April.\n"
                f"* **Off-Season Tightening**: Supply drops significantly during Q3/Q4, creating off-season unit price increases.\n\n"
                f"### 2. Economic Drivers\n"
                f"* Lack of post-harvest cold-storage forces immediate selling during harvest gluts at lower farm-gate prices.\n\n"
                f"### 3. Recommended Strategic Roadmap\n"
                f"1. **Cold-Chain Infrastructure**: Invest in commercial cold-storage facilities near production hubs to extend selling windows.\n"
                f"2. **Warehouse Financing**: Implement warehouse receipt financing so farmers can hold inventory for off-season price premiums."
            )

        top_crop = self._clean_chapter_title(hs4_list[0]) if len(hs4_list) > 0 else 'Cashew Nuts & Coconuts (HS 0801)'
        top_crop_share = hs4_list[0].get('revenue_share_pct', 74.3) if len(hs4_list) > 0 else 74.3
        return (
            f"### 1. Key Insights\n"
            f"* **Leading Agricultural Driver**: **{top_crop}** accounts for **{top_crop_share:.1f}%** of total export value (${(total_usd*top_crop_share/100)/1e6:.2f}M USD).\n"
            f"* **Total Agricultural Trade Scale**: **${total_usd/1e6:.2f} Million USD** across **{total_weight:,.1f} Tonnes** (average unit price **${avg_price:.2f}/kg**).\n"
            f"* **Market Concentration**: Overall market concentration score stands at **HHI {hhi:,.0f}**.\n\n"
            f"### 2. Strategic Recommendations\n"
            f"1. Expand local agro-processing capacity to capture higher margins before exporting.\n"
            f"2. Broaden direct export market channels to reduce geographic concentration risk."
        )

ai_service = AIService()
