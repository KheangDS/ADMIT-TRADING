import re
from fastapi import APIRouter
from app.models.schemas import ChatRequest, ChatResponse
from app.api.v1.endpoints.upload import SESSION_STORE
from app.services.etl_service import ETLService
from app.services.duckdb_service import duckdb_service
from app.services.ai_service import ai_service


from app.services.exchange_rate_service import exchange_rate_service

router = APIRouter()

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
        
    # Execute query in DuckDB against active session or persistent master table
    sql_executed = None
    data_points = None
    
    try:
        # Check if user mentioned a specific 4-digit HS code (e.g., 0904, 0801, 0804, 0910, 1211)
        hs_match = re.search(r'\b(0\d{3}|\d{4})\b', question)
        
        if hs_match:
            matched_code = hs_match.group(1)
            sql_executed = (
                f"SELECT hs8_code, hs8_desc, product_name, "
                f"ROUND(SUM(weight_kg)/1000, 2) AS volume_ton, "
                f"ROUND(SUM(val_khr)/{rate_val}, 2) AS val_usd, "
                f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS price_usd_per_kg "
                f"FROM trade_data WHERE hs4_code = '{matched_code}' "
                f"GROUP BY hs8_code, hs8_desc, product_name ORDER BY val_usd DESC"
            )
        else:
            sql_executed = (
                f"SELECT hs4_code, hs4_desc, "
                f"ROUND(SUM(weight_kg)/1000, 2) AS volume_ton, "
                f"ROUND(SUM(val_khr)/{rate_val}, 2) AS val_usd, "
                f"ROUND((SUM(val_khr)/{rate_val}) / NULLIF(SUM(weight_kg), 0), 3) AS price_usd_per_kg "
                f"FROM trade_data GROUP BY hs4_code, hs4_desc ORDER BY val_usd DESC"
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
