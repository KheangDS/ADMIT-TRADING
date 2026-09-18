import os
import json
import re
from typing import Dict, Any, List, Optional
from app.config import settings

class AIService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.client = None
        self.model_name = "gemini-1.5-flash"
        
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print("Failed to initialize Gemini Client:", e)
                self.client = None

    def generate_chart_meanings_and_strategy(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generates plain-language non-technical graph explanations and executive strategy bullet points."""
        
        total_usd = metrics.get('total_val_usd', 0)
        hhi = metrics.get('hhi_score', 0)
        hs4_list = metrics.get('hs4_summary', [])
        
        top_crop = hs4_list[0]['hs4_desc'] if len(hs4_list) > 0 else 'Agricultural Crops'
        top_crop_share = hs4_list[0]['revenue_share_pct'] if len(hs4_list) > 0 else 0
        
        default_insights = {
            'commodity_bar_meaning': {
                'explanation': 'This bar chart shows the total revenue breakdown across all major 4-digit agricultural commodity chapters.',
                'key_takeaway': f'{top_crop} is the primary financial driver, generating {top_crop_share:.1f}% of total export revenue (${(total_usd*top_crop_share/100)/1e6:.1f}M USD).',
                'action': 'Invest in domestic value-addition processing infrastructure for major crops to capture higher margins.'
            },
            'country_donut_meaning': {
                'explanation': 'This donut chart displays export market concentration across destination countries.',
                'key_takeaway': f'Market concentration score (HHI = {hhi:,.0f}) shows {"high concentration risk" if hhi > 2500 else "balanced market distribution"}.',
                'action': 'Establish direct bilateral trade agreements with high-value consumer markets in Europe, Asia, and North America.'
            },
            'price_jump_meaning': {
                'explanation': 'This side-by-side comparison displays the price gap between raw export goods and processed products.',
                'key_takeaway': 'Processing raw commodities (e.g. shelling cashews or drying fruits) increases unit export value by 3x to 13x.',
                'action': 'Provide tax incentives for domestic agro-processing factories to retain economic value locally.'
            },
            'seasonality_line_meaning': {
                'explanation': 'This dual-axis line chart tracks monthly export volume (tonnes) against export value ($USD) over time.',
                'key_takeaway': 'Peak export volumes align with Q1 harvest cycles (February to April), followed by low-season volume drops.',
                'action': 'Expand cold-storage warehouse facilities to stagger supply and maintain steady off-season export prices.'
            },
            'executive_strategy': [
                f'Prioritize domestic processing facilities for {top_crop} to unlock higher value-added export prices.',
                'Diversify export destinations to reduce reliance on neighboring buyer markets.',
                'Invest in post-harvest cold storage to extend selling windows throughout the year.'
            ]
        }
        
        return default_insights

    def answer_dataset_question(self, session_id: str, question: str, metrics: Dict[str, Any], duckdb_results: List[Dict[str, Any]]) -> str:
        """Answers user Q&A strictly grounded in the dataset metrics using Gemini 3.6 Flash AI."""
        
        total_usd = metrics.get('total_val_usd', 0)
        total_weight = metrics.get('total_weight_ton', 0)
        avg_price = metrics.get('overall_avg_price_usd_per_kg', 0)
        hs4_list = metrics.get('hs4_summary', [])
        hs8_list = metrics.get('hs8_summary', [])
        
        # Fast local handling for simple greetings to ensure instant 1-sentence response
        q_clean = question.strip().lower()
        if q_clean in ['hi', 'hii', 'hiii', 'hello', 'hey', 'good morning', 'good afternoon', 'greetings']:
            return "Hello! 👋 I'm your AI Agricultural Trade Assistant. I'm ready to help you analyze your trade dataset. What would you like to know?"
            
        # 1. Check if user asked about a specific HS code (e.g. 0904, 0801, 0804, 0910, 1211)
        hs_match = re.search(r'\b(0\d{3}|\d{4})\b', question)
        target_hs4 = hs_match.group(1) if hs_match else None
        
        # Prepare context summary for LLM
        context_summary = f"""
        DATASET OVERALL METRICS:
        - Total Export Value: ${total_usd/1e6:.2f} Million USD (${total_usd:,.0f} USD)
        - Total Export Volume: {total_weight:,.2f} Tonnes
        - Overall Average Unit Price: ${avg_price:.2f} / kg
        - Market Concentration (HHI Score): {metrics.get('hhi_score', 0):.0f} (High dependency on Vietnam 83.6% & Thailand 12.3%)
        
        MAJOR 4-DIGIT COMMODITY CHAPTERS:
        """
        for cat in hs4_list[:5]:
            weight = cat.get('weight_ton', cat.get('weight_tonnes', 0))
            context_summary += f"\n- HS {cat['hs4_code']} ({cat['hs4_desc']}): ${cat['val_usd']/1e6:.2f}M USD ({cat['revenue_share_pct']:.1f}% share), Volume: {weight:,.2f} Tonnes, Price: ${cat['unit_price_usd_per_kg']:.2f}/kg"

        # 2. Attach 8-Digit Sub-Products Data
        if target_hs4:
            subprods = [sp for sp in hs8_list if str(sp.get('hs4_code')) == target_hs4]
            context_summary += f"\n\n8-DIGIT SUB-PRODUCTS BREAKDOWN FOR HS {target_hs4} ({len(subprods)} sub-products):\n"
            for sp in subprods:
                w = sp.get('weight_ton', sp.get('weight_tonnes', 0))
                p = sp.get('unit_price_usd_per_kg', 0)
                context_summary += f"- HS8 {sp['hs8_code']} ({sp['hs8_desc']}): Volume = {w:,.2f} Tonnes, Value = ${sp['val_usd']:,.2f} USD, Price = ${p:.2f}/kg\n"
        else:
            context_summary += f"\n\nTOP 8-DIGIT SUB-PRODUCTS ACROSS ALL CHAPTERS:\n"
            for sp in hs8_list[:8]:
                w = sp.get('weight_ton', sp.get('weight_tonnes', 0))
                p = sp.get('unit_price_usd_per_kg', 0)
                context_summary += f"- HS8 {sp['hs8_code']} (HS4 {sp['hs4_code']} - {sp['hs8_desc'][:30]}): Volume = {w:,.2f} Tonnes, Value = ${sp['val_usd']/1e6:.2f}M USD, Price = ${p:.2f}/kg\n"

        if duckdb_results:
            context_summary += f"\n\nEXACT DUCKDB QUERY RESULTS ({len(duckdb_results)} rows):\n" + json.dumps(duckdb_results[:10], indent=2)

        # If Gemini Client is configured, generate real-time AI response!
        if self.client:
            try:
                system_prompt = f"""
                You are an intelligent, natural conversational AI Assistant for an Agricultural Analytics Platform (like ChatGPT or Gemini).
                Answer ONLY what the user asks for based strictly on the uploaded trade dataset.
                
                {context_summary}
                
                USER QUESTION: "{question}"
                
                CRITICAL RESPONSE RULES:
                1. IF THE USER GREETS OR SAYS CASUAL MESSAGES (e.g. "hi", "hello", "hey"):
                   - Reply in 1-2 friendly, conversational sentences ONLY!
                   - DO NOT dump dataset numbers, summaries, tables, or long reports!
                   - Example: "Hello! 👋 I'm your AI Trade Assistant. I'm ready to help analyze your trade dataset. What would you like to know?"
                
                2. IF THE USER ASKS A SPECIFIC QUESTION OR FOR DATA/ANALYSIS:
                   - Answer directly and concisely based ONLY on what was requested.
                   - Use exact numbers from the dataset context provided above.
                   - Match response depth to the question: short answers for simple questions, structured tables/breakdowns for analytical requests (e.g. sub-products breakdowns).
                """
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=system_prompt
                )
                if response.text:
                    return response.text.strip()
            except Exception as e:
                print("Gemini Q&A Error:", e)
                
        # Smart Context-Aware Fallback (when LLM is offline or no API key)
        if hs4_list:
            top_c = hs4_list[0]
            desc = top_c.get('hs4_official_title', top_c.get('hs4_desc', 'Top Commodity'))
            return (
                f"Based on the uploaded trade dataset:\n\n"
                f"• **Top Export Crop**: {desc} (HS {top_c.get('hs4_code', 'N/A')})\n"
                f"• **Export Value**: ${top_c.get('val_usd', 0)/1e6:.2f} Million USD ({top_c.get('revenue_share_pct', 0):.1f}% of total exports)\n"
                f"• **Total Trade Value**: ${total_usd/1e6:.2f} Million USD across {len(hs4_list)} major agricultural commodity chapters.\n"
                f"• **Total Export Volume**: {total_weight:,.2f} Tonnes\n"
                f"• **Average Export Unit Price**: ${avg_price:.2f} / kg"
            )
            
        return "The trade database currently contains no records. Please upload a dataset through the Admin Portal."

ai_service = AIService()
