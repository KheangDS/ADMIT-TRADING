import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.router import api_router
from app.services.duckdb_service import duckdb_service
from app.services.etl_service import ETLService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-seed persistent DuckDB if database is currently empty
    try:
        count = duckdb_service.get_records_count()
        if count == 0:
            dataset_candidates = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Dataset.xlsx"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Dataset.xlsx"),
                "Dataset.xlsx"
            ]
            for candidate in dataset_candidates:
                if os.path.exists(candidate):
                    print(f"[DuckDB Startup] Auto-seeding initial persistent dataset from: {candidate}")
                    with open(candidate, "rb") as f:
                        content = f.read()
                    df_raw = ETLService.inspect_and_load_file(content, os.path.basename(candidate))
                    is_valid, _, col_map = ETLService.validate_trade_schema(df_raw)
                    if is_valid:
                        df_clean, metrics = ETLService.process_trade_data(df_raw, col_map, exchange_rate=4000.0)
                        inserted, updated, total = duckdb_service.upsert_dataframe(df_clean)
                        period_str = f"{metrics.get('begin_date', 'Jan 2023')} – {metrics.get('end_date', 'Mar 2024')}"
                        duckdb_service.record_upload(os.path.basename(candidate), inserted, updated, total, period_str)
                        print(f"[DuckDB Startup] Seeded successfully! Total records in persistent storage: {total}")
                    break
        else:
            # Ensure upload history has baseline entry if records already existed
            duckdb_service.get_upload_history()
    except Exception as e:
        print(f"[DuckDB Startup] Note: Could not auto-seed baseline data: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API V1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs"
    }


def start():
    """Starts the Uvicorn development server."""
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host=host, port=port, reload=True, reload_dirs=["app"])


if __name__ == "__main__":
    start()
