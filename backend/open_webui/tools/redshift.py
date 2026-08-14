"""
Redshift query tool for Open WebUI.

Connects directly to the company Redshift warehouse via psycopg (v3), which
is already a project dependency and speaks the same wire protocol Redshift
uses (Postgres-compatible).
"""

import json
import logging
import re

import psycopg

from open_webui.env import (
    REDSHIFT_MAX_ROWS,
    REDSHIFT_STATEMENT_TIMEOUT_MS,
    REDSHIFT_URL,
)

log = logging.getLogger(__name__)

_BLOCKED_KEYWORDS = (
    'INSERT',
    'UPDATE',
    'DELETE',
    'DROP',
    'ALTER',
    'TRUNCATE',
    'GRANT',
    'REVOKE',
    'CREATE',
    'COPY',
    'UNLOAD',
    'VACUUM',
    'MERGE',
    'CALL',
)
_BLOCKED_KEYWORDS_RE = re.compile(r'\b(' + '|'.join(_BLOCKED_KEYWORDS) + r')\b', re.IGNORECASE)


class ReadOnlySQLError(ValueError):
    pass


def _ensure_read_only_sql(query: str) -> None:
    """Raise ReadOnlySQLError if query contains a write/DDL keyword as a whole word.

    # ponytail: coarse whole-word keyword blocklist, not a real SQL parser — a column
    # literally named e.g. "update" would false-positive. Upgrade to a real SQL parser
    # (e.g. sqlglot) if that ever bites in practice.
    """
    match = _BLOCKED_KEYWORDS_RE.search(query)
    if match:
        raise ReadOnlySQLError(
            f'Query contains a disallowed keyword: {match.group(1).upper()}. '
            'Only read-only SELECT/EXPLAIN queries are permitted.'
        )


async def _connect() -> psycopg.AsyncConnection:
    if not REDSHIFT_URL:
        raise RuntimeError('REDSHIFT_URL is not configured')
    return await psycopg.AsyncConnection.connect(
        REDSHIFT_URL,
        autocommit=True,
        connect_timeout=10,
        options=(
            f'-c statement_timeout={REDSHIFT_STATEMENT_TIMEOUT_MS} -c default_transaction_read_only=on'
        ),
    )


async def redshift_test_connection() -> str:
    """
    Test connectivity to the Redshift warehouse.

    :return: JSON with connection status, and the Redshift version if successful
    """
    try:
        async with await _connect() as conn:
            async with conn.cursor() as cur:
                await cur.execute('SELECT version();')
                row = await cur.fetchone()
        return json.dumps({'status': 'ok', 'version': row[0] if row else None})
    except Exception as e:
        log.warning(f'redshift_test_connection error: {e}')
        return json.dumps({'status': 'error', 'error': str(e)})


async def redshift_list_schemas() -> str:
    """
    List all queryable schemas in the Redshift warehouse.

    :return: JSON array of schema names
    """
    try:
        async with await _connect() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT nspname FROM pg_namespace "
                    "WHERE nspname NOT LIKE 'pg\\_%' AND nspname != 'information_schema' "
                    "ORDER BY nspname;"
                )
                rows = await cur.fetchall()
        return json.dumps([r[0] for r in rows])
    except Exception as e:
        log.warning(f'redshift_list_schemas error: {e}')
        return json.dumps({'error': str(e)})


async def redshift_list_tables_in_schema(schema: str) -> str:
    """
    List tables and views in a given Redshift schema.

    Before querying a table in the public schema, check whether an equivalent staging view
    exists in analytics_staging (named like stg_<source>__<table>) and query that instead if
    it exists — it is cheaper to scan.

    :param schema: The schema name to list tables for (e.g. "public", "analytics_marts")
    :return: JSON array of {table_name, table_type}
    """
    try:
        async with await _connect() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    'SELECT table_name, table_type FROM information_schema.tables '
                    'WHERE table_schema = %s ORDER BY table_name;',
                    (schema,),
                )
                rows = await cur.fetchall()
        return json.dumps([{'table_name': r[0], 'table_type': r[1]} for r in rows])
    except Exception as e:
        log.warning(f'redshift_list_tables_in_schema error: {e}')
        return json.dumps({'error': str(e)})


async def redshift_explain_query(query: str) -> str:
    """
    Show the query plan Redshift would use for a read-only SQL query, without running it.
    Use this to check a query's cost before running it with redshift_run_query.

    Before querying a table in the public schema, check whether an equivalent staging view
    exists in analytics_staging (named like stg_<source>__<table>) and query that instead if
    it exists — it is cheaper to scan.

    :param query: The SQL SELECT query to explain
    :return: JSON with the plan lines, or an error
    """
    try:
        _ensure_read_only_sql(query)
        async with await _connect() as conn:
            async with conn.cursor() as cur:
                await cur.execute(f'EXPLAIN {query}')
                rows = await cur.fetchall()
        return json.dumps({'plan': [r[0] for r in rows]})
    except ReadOnlySQLError as e:
        return json.dumps({'error': str(e)})
    except Exception as e:
        log.warning(f'redshift_explain_query error: {e}')
        return json.dumps({'error': str(e)})


async def redshift_run_query(query: str, max_rows: int = None) -> str:
    """
    Run a read-only SQL query against the Redshift warehouse and return the results. Only
    SELECT-style queries are allowed — INSERT/UPDATE/DELETE/DROP/ALTER/etc. are rejected.

    Before querying a table in the public schema, check whether an equivalent staging view
    exists in analytics_staging (named like stg_<source>__<table>) and query that instead if
    it exists — it is cheaper to scan.

    :param query: The SQL SELECT query to run
    :param max_rows: Maximum rows to return (default and hard ceiling: server-configured)
    :return: JSON with columns, rows, row_count, and whether results were truncated
    """
    try:
        _ensure_read_only_sql(query)
        limit = REDSHIFT_MAX_ROWS if max_rows is None else max(1, min(max_rows, REDSHIFT_MAX_ROWS))

        async with await _connect() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query)
                columns = [desc.name for desc in cur.description] if cur.description else []
                rows = await cur.fetchmany(limit + 1)

        truncated = len(rows) > limit
        rows = rows[:limit]

        return json.dumps(
            {
                'columns': columns,
                'rows': [list(row) for row in rows],
                'row_count': len(rows),
                'truncated': truncated,
            },
            default=str,
        )
    except ReadOnlySQLError as e:
        return json.dumps({'error': str(e)})
    except Exception as e:
        log.warning(f'redshift_run_query error: {e}')
        return json.dumps({'error': str(e)})
