from app.services.etl_service import ETLService
from app.services.ai_service import ai_service

def main():
    with open('../Dataset.xlsx', 'rb') as f:
        contents = f.read()
    
    df_raw = ETLService.inspect_and_load_file(contents, 'Dataset.xlsx')
    is_valid, msg, col_map = ETLService.validate_trade_schema(df_raw)
    print("Is Valid Schema:", is_valid)
    print("Validation Msg:", msg)
    
    # 1. Process at 4000 KHR / USD
    df_clean, metrics_4000 = ETLService.process_trade_data(df_raw, col_map, exchange_rate=4000.0)
    print("\n--- METRICS @ $1 USD = 4,000 KHR ---")
    print(f"Total Weight: {metrics_4000['total_weight_ton']:,.2f} Tonnes")
    print(f"Total Value (USD): ${metrics_4000['total_val_usd']/1e6:,.2f} Million USD")
    print(f"Total Value (KHR): {metrics_4000['total_val_khr']/1e9:,.2f} Billion KHR")
    print(f"Overall Avg Unit Price: ${metrics_4000['overall_avg_price_usd_per_kg']:.2f} / kg")
    print(f"Market Concentration HHI Score: {metrics_4000['hhi_score']:.1f}")
    print(f"HS4 Chapter Count: {len(metrics_4000['hs4_summary'])}")
    
    for cat in metrics_4000['hs4_summary']:
        print(f"  - HS {cat['hs4_code']} ({cat['hs4_desc']}): ${cat['val_usd']/1e6:,.2f}M USD ({cat['revenue_share_pct']:.1f}% share)")

    # 3. Test Persistent DuckDB Upsert
    from app.services.duckdb_service import duckdb_service
    inserted, updated, total = duckdb_service.upsert_dataframe(df_clean)
    print(f"\n--- DUCKDB PERSISTENT UPSERT ---")
    print(f"Rows Inserted: {inserted}, Rows Updated: {updated}, Total Records: {total}")
    
    # Re-run upsert to verify non-destructive update behavior
    inserted2, updated2, total2 = duckdb_service.upsert_dataframe(df_clean)
    print(f"Second Upsert (Same Data): Inserted={inserted2}, Updated={updated2}, Total Records={total2}")
    
    # Master query verification
    df_m = duckdb_service.get_master_dataframe()
    print(f"Master DataFrame Loaded from DuckDB: {len(df_m)} rows")

if __name__ == "__main__":
    main()
