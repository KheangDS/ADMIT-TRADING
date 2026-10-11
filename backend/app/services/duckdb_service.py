"""Ephemeral, request-local DuckDB. Never opens or mutates the legacy database."""
import re
import duckdb


class DuckDBService:
    def execute_scoped(self, frame, sql_query, parameters=None):
        """Execute trusted server-built SELECT over only the provided scoped frame.

        Literal values are supplied through parameters. External file/network access,
        extension autoload/install and multiple statements are disabled. SQL failures
        propagate; they never become unrelated first-ten-row results.
        """
        if not re.match(r'^\s*SELECT\b', sql_query, re.I) or any(token in sql_query for token in (';', '--', '/*')):
            raise ValueError('Only a single server-built SELECT is permitted')
        if re.search(r'\b(read_csv|read_parquet|read_json|sqlite_scan|postgres_scan|httpfs|query|query_table|glob|attach|install|load|pragma|copy)\b', sql_query, re.I):
            raise ValueError('External and dynamic SQL sources are forbidden')
        with duckdb.connect(':memory:', config={'enable_external_access': False, 'autoinstall_known_extensions': False,
                                               'autoload_known_extensions': False, 'threads': 1}) as connection:
            connection.register('trade_data', frame)
            result = connection.execute(sql_query, parameters or []).df()
            # Convert NaN/NULL to JSON null, never nonfinite JSON numbers.
            return result.astype(object).where(result.notna(), None).to_dict(orient='records')

    def get_master_dataframe(self):
        raise RuntimeError('Legacy master access is disabled; use publication-scoped_frame')

    def register_dataset(self, session_id, frame):
        raise RuntimeError('Public/private session dataset registration is disabled; use staged imports')

    def execute_sql(self, session_id, sql_query):
        raise RuntimeError('Client session_id cannot select a dataset; use execute_scoped')

    def upsert_dataframe(self, frame):
        raise RuntimeError('Legacy writes are disabled; create an immutable trade revision')


# Stateless helper only, not a connection or frame cache.
duckdb_service = DuckDBService()
