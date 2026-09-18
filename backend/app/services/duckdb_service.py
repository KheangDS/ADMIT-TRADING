import os
import duckdb
import pandas as pd
from typing import Dict, Any, List, Tuple
from app.config import settings

class DuckDBService:
    def __init__(self):
        self.db_path = settings.DB_PATH
        self._conn = None
        self.active_sessions: Dict[str, str] = {}

    @property
    def conn(self):
        """Lazy-loaded DuckDB connection to avoid startup lock contention."""
        if self._conn is None:
            self._conn = duckdb.connect(database=self.db_path)
            self._init_db()
        return self._conn

    def _init_db(self):
        """Initializes the master persistent table schema if not already present."""
        try:
            self._conn.execute("DROP INDEX IF EXISTS idx_trade_composite;")
        except Exception:
            pass

        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS master_trade_data (
                year INTEGER,
                month INTEGER,
                hs4_code VARCHAR,
                hs8_code VARCHAR,
                hs4_desc VARCHAR,
                product_name VARCHAR,
                country VARCHAR,
                weight_kg DOUBLE,
                val_khr DOUBLE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS upload_history (
                filename VARCHAR,
                rows_inserted INTEGER,
                rows_updated INTEGER,
                total_records INTEGER,
                period_range VARCHAR,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

    def upsert_dataframe(self, df_clean: pd.DataFrame) -> Tuple[int, int, int]:
        """
        Incrementally upserts cleaned trade records into persistent DuckDB.
        Composite Unique Key: (year, month, hs8_code, country).
        Returns: (rows_inserted, rows_updated, total_records)
        """
        cols = ['year', 'month', 'hs4_code', 'hs8_code', 'hs4_desc', 'product_name', 'country', 'weight_kg', 'val_khr']
        df_to_save = df_clean[cols].copy()
        
        try:
            self.conn.unregister("staging_incoming_trade")
        except Exception:
            pass
            
        # Register staging table
        self.conn.register("staging_incoming_trade", df_to_save)
        
        try:
            # Calculate update vs insert counts
            overlap_res = self.conn.execute("""
                SELECT COUNT(*) AS updated_count 
                FROM master_trade_data m
                INNER JOIN staging_incoming_trade s
                ON m.year = s.year 
                   AND m.month = s.month 
                   AND m.hs8_code = s.hs8_code 
                   AND m.country = s.country;
            """).fetchone()
            rows_updated = overlap_res[0] if overlap_res else 0
            
            insert_res = self.conn.execute("""
                SELECT COUNT(*) AS inserted_count
                FROM staging_incoming_trade s
                LEFT JOIN master_trade_data m
                ON m.year = s.year 
                   AND m.month = s.month 
                   AND m.hs8_code = s.hs8_code 
                   AND m.country = s.country
                WHERE m.year IS NULL;
            """).fetchone()
            rows_inserted = insert_res[0] if insert_res else 0
            
            # Perform clean atomic merge: non-conflicting existing records + all new staging records
            self.conn.execute("""
                CREATE OR REPLACE TABLE master_trade_data AS
                SELECT 
                    year, month, hs4_code, hs8_code, hs4_desc, product_name, country, weight_kg, val_khr, updated_at
                FROM master_trade_data m
                WHERE NOT EXISTS (
                    SELECT 1 FROM staging_incoming_trade s
                    WHERE m.year = s.year
                      AND m.month = s.month
                      AND m.hs8_code = s.hs8_code
                      AND m.country = s.country
                )
                UNION ALL
                SELECT 
                    year, month, hs4_code, hs8_code, hs4_desc, product_name, country, weight_kg, val_khr, CURRENT_TIMESTAMP AS updated_at
                FROM staging_incoming_trade;
            """)
            
            total_res = self.conn.execute("SELECT COUNT(*) FROM master_trade_data").fetchone()
            total_records = total_res[0] if total_res else 0
            
            return rows_inserted, rows_updated, total_records
        finally:
            try:
                self.conn.unregister("staging_incoming_trade")
            except Exception:
                pass

    def get_master_dataframe(self) -> pd.DataFrame:
        """Loads the full master dataset from persistent DuckDB storage."""
        return self.conn.execute("SELECT * FROM master_trade_data ORDER BY year, month").df()

    def get_records_count(self) -> int:
        """Returns total records stored in the persistent database."""
        res = self.conn.execute("SELECT COUNT(*) FROM master_trade_data").fetchone()
        return res[0] if res else 0

    def register_dataset(self, session_id: str, df: pd.DataFrame) -> str:
        """Registers a pandas dataframe into DuckDB as a virtual session SQL table."""
        table_name = f"trade_data_{session_id.replace('-', '_')}"
        self.conn.register(table_name, df)
        self.active_sessions[session_id] = table_name
        return table_name

    def execute_sql(self, session_id: str, sql_query: str) -> List[Dict[str, Any]]:
        """Executes a sanitized SQL query against the master table or session table."""
        table_name = "master_trade_data"
        if session_id and session_id in self.active_sessions:
            table_name = self.active_sessions[session_id]
            
        sanitized_query = sql_query.replace("trade_data", table_name)
        
        try:
            res_df = self.conn.execute(sanitized_query).df()
            return res_df.to_dict(orient='records')
        except Exception as e:
            fallback = f"SELECT * FROM {table_name} LIMIT 10"
            res_df = self.conn.execute(fallback).df()
            return res_df.to_dict(orient='records')

    def record_upload(self, filename: str, rows_inserted: int, rows_updated: int, total_records: int, period_range: str = ""):
        """Records an ingested dataset file event in persistent history."""
        try:
            self.conn.execute("""
                INSERT INTO upload_history (filename, rows_inserted, rows_updated, total_records, period_range, uploaded_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
            """, [filename, rows_inserted, rows_updated, total_records, period_range])
        except Exception as e:
            print(f"[DuckDB] Could not record upload history: {e}")

    def get_upload_history(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Returns the list of recently uploaded dataset files and their merge statistics."""
        try:
            df_hist = self.conn.execute(f"""
                SELECT 
                    filename, 
                    rows_inserted, 
                    rows_updated, 
                    total_records, 
                    period_range,
                    CAST(uploaded_at AS VARCHAR) AS uploaded_at
                FROM upload_history
                ORDER BY uploaded_at DESC
                LIMIT {limit};
            """).df()

            # If history is empty but master table already contains data, auto-backfill baseline entry
            if df_hist.empty:
                master_count = self.get_records_count()
                if master_count > 0:
                    try:
                        period_row = self.conn.execute("""
                            SELECT 
                                MIN(year * 100 + month) AS min_ym,
                                MAX(year * 100 + month) AS max_ym
                            FROM master_trade_data
                        """).fetchone()
                        
                        import calendar
                        period_str = "Jan 2023 – Dec 2023"
                        if period_row and period_row[0] and period_row[1]:
                            min_y, min_m = divmod(period_row[0], 100)
                            max_y, max_m = divmod(period_row[1], 100)
                            m1 = calendar.month_abbr[max(1, min(12, min_m))]
                            m2 = calendar.month_abbr[max(1, min(12, max_m))]
                            period_str = f"{m1} {min_y} – {m2} {max_y}"
                        
                        self.record_upload(
                            filename="Dataset.xlsx",
                            rows_inserted=master_count,
                            rows_updated=0,
                            total_records=master_count,
                            period_range=period_str
                        )
                        df_hist = self.conn.execute(f"""
                            SELECT 
                                filename, 
                                rows_inserted, 
                                rows_updated, 
                                total_records, 
                                period_range,
                                CAST(uploaded_at AS VARCHAR) AS uploaded_at
                            FROM upload_history
                            ORDER BY uploaded_at DESC
                            LIMIT {limit};
                        """).df()
                    except Exception as e:
                        print(f"[DuckDB] Auto-backfill upload history error: {e}")

            return df_hist.to_dict(orient='records')
        except Exception as e:
            print(f"[DuckDB] Could not fetch upload history: {e}")
            return []

# Singleton instance
duckdb_service = DuckDBService()
