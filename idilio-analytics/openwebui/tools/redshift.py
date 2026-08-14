"""
title: Redshift Analytics
author: Idilio
description: Query the Redshift data warehouse directly -- schema/table browsing, EXPLAIN, and read-only SELECT with a server-side row cap. Backs the Idilio Analytics skill.
required_open_webui_version: 0.5.0
version: 0.1.0
"""

import json
import logging
import os
import re
from typing import Optional

import psycopg
from pydantic import BaseModel, Field

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
    'INTO',
)
_BLOCKED_KEYWORDS_RE = re.compile(r'\b(' + '|'.join(_BLOCKED_KEYWORDS) + r')\b', re.IGNORECASE)


class ReadOnlySQLError(ValueError):
    pass


def _ensure_read_only_sql(query: str) -> None:
    """Raise ReadOnlySQLError if query contains a write/DDL keyword as a whole word,
    stacks multiple statements, or starts with ANALYZE.

    # ponytail: coarse whole-word keyword blocklist, not a real SQL parser -- a column
    # literally named e.g. "update" would false-positive. Upgrade to a real SQL parser
    # (e.g. sqlglot) if that ever bites in practice.
    """
    stripped = query.strip()
    # Allow exactly one trailing semicolon (LLMs commonly emit one), but reject
    # anything else containing a ';' -- that's statement stacking, e.g.
    # "SELECT 1; SELECT * FROM secrets", which no single blocked keyword catches.
    body = stripped[:-1] if stripped.endswith(';') else stripped
    if ';' in body:
        raise ReadOnlySQLError(
            'Query contains multiple statements separated by ";". '
            'Only a single read-only SELECT/EXPLAIN query is permitted.'
        )

    first_word_match = re.match(r'^\s*([A-Za-z_]+)', query)
    if first_word_match and first_word_match.group(1).upper() == 'ANALYZE':
        raise ReadOnlySQLError(
            'Query starts with ANALYZE, which is not permitted (EXPLAIN ANALYZE would '
            'actually execute the query instead of just planning it).'
        )

    match = _BLOCKED_KEYWORDS_RE.search(query)
    if match:
        raise ReadOnlySQLError(
            f'Query contains a disallowed keyword: {match.group(1).upper()}. '
            'Only read-only SELECT/EXPLAIN queries are permitted.'
        )


def _redshift_url() -> str:
    # REDSHIFT_URL stays an env var, not a Valve -- it's a credential, and every other
    # secret in this app (OPENAI_API_KEY, WEBUI_SECRET_KEY, etc.) is env-var-only too.
    url = os.environ.get('REDSHIFT_URL')
    if not url:
        raise RuntimeError('REDSHIFT_URL is not configured')
    if url.startswith('postgres://'):
        url = 'postgresql://' + url[len('postgres://') :]
    return url


class Tools:
    class Valves(BaseModel):
        STATEMENT_TIMEOUT_MS: int = Field(
            default=30000,
            description='Per-query timeout in milliseconds, enforced by Redshift itself.',
        )
        MAX_ROWS: int = Field(
            default=200,
            description='Hard ceiling on rows returned by run_query/explain_query, regardless of what the caller requests.',
        )

    def __init__(self):
        self.valves = self.Valves()

    async def _connect(self) -> psycopg.AsyncConnection:
        return await psycopg.AsyncConnection.connect(
            _redshift_url(),
            autocommit=True,
            connect_timeout=10,
            options=(
                f'-c statement_timeout={self.valves.STATEMENT_TIMEOUT_MS} '
                '-c default_transaction_read_only=on'
            ),
        )

    async def test_connection(self) -> str:
        """
        Test connectivity to the Redshift warehouse.

        :return: JSON with connection status, and the Redshift version if successful
        """
        try:
            async with await self._connect() as conn:
                async with conn.cursor() as cur:
                    await cur.execute('SELECT version();')
                    row = await cur.fetchone()
            return json.dumps({'status': 'ok', 'version': row[0] if row else None})
        except Exception as e:
            log.warning(f'test_connection error: {e}')
            return json.dumps({'status': 'error', 'error': str(e)})

    async def list_schemas(self) -> str:
        """
        List all queryable schemas in the Redshift warehouse.

        :return: JSON array of schema names
        """
        try:
            async with await self._connect() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "SELECT nspname FROM pg_namespace "
                        "WHERE nspname NOT LIKE 'pg\\_%' AND nspname != 'information_schema' "
                        "ORDER BY nspname;"
                    )
                    rows = await cur.fetchall()
            return json.dumps([r[0] for r in rows])
        except Exception as e:
            log.warning(f'list_schemas error: {e}')
            return json.dumps({'error': str(e)})

    async def list_tables_in_schema(self, schema: str) -> str:
        """
        List tables and views in a given Redshift schema.

        Before querying a table in the public schema, check whether an equivalent staging
        view exists in analytics_staging (named like stg_<source>__<table>) and query that
        instead if it exists -- it is cheaper to scan.

        :param schema: The schema name to list tables for (e.g. "public", "analytics_marts")
        :return: JSON array of {table_name, table_type}
        """
        try:
            async with await self._connect() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        'SELECT table_name, table_type FROM information_schema.tables '
                        'WHERE table_schema = %s ORDER BY table_name;',
                        (schema,),
                    )
                    rows = await cur.fetchall()
            return json.dumps([{'table_name': r[0], 'table_type': r[1]} for r in rows])
        except Exception as e:
            log.warning(f'list_tables_in_schema error: {e}')
            return json.dumps({'error': str(e)})

    async def explain_query(self, query: str) -> str:
        """
        Show the query plan Redshift would use for a read-only SQL query, without running it.
        Use this to check a query's cost before running it with run_query.

        Before querying a table in the public schema, check whether an equivalent staging
        view exists in analytics_staging (named like stg_<source>__<table>) and query that
        instead if it exists -- it is cheaper to scan.

        :param query: The SQL SELECT query to explain
        :return: JSON with the plan lines, or an error
        """
        try:
            _ensure_read_only_sql(query)
            async with await self._connect() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(f'EXPLAIN {query}')
                    # ponytail: EXPLAIN output is normally a handful of plan lines, so a
                    # client-side cursor is fine here -- this fetchmany cap is just a
                    # backstop in case the keyword blocklist above ever has a hole.
                    rows = await cur.fetchmany(self.valves.MAX_ROWS)
            return json.dumps({'plan': [r[0] for r in rows]})
        except ReadOnlySQLError as e:
            return json.dumps({'error': str(e)})
        except Exception as e:
            log.warning(f'explain_query error: {e}')
            return json.dumps({'error': str(e)})

    async def run_query(self, query: str, max_rows: Optional[int] = None) -> str:
        """
        Run a read-only SQL query against the Redshift warehouse and return the results. Only
        SELECT-style queries are allowed -- INSERT/UPDATE/DELETE/DROP/ALTER/etc. are rejected.

        Before querying a table in the public schema, check whether an equivalent staging
        view exists in analytics_staging (named like stg_<source>__<table>) and query that
        instead if it exists -- it is cheaper to scan.

        :param query: The SQL SELECT query to run
        :param max_rows: Maximum rows to return (default and hard ceiling: admin-configured)
        :return: JSON with columns, rows, row_count, and whether results were truncated
        """
        try:
            _ensure_read_only_sql(query)
            cap = self.valves.MAX_ROWS
            limit = cap if max_rows is None else max(1, min(max_rows, cap))

            async with await self._connect() as conn:
                # Server-side (named) cursor: fetchmany() below then only pulls `limit + 1`
                # rows from Redshift instead of buffering the entire result set client-side
                # first. withhold=True is required -- on this autocommit connection a plain
                # named cursor fails outright ("DECLARE CURSOR can only be used in
                # transaction blocks"), since a non-held cursor is dropped the instant its
                # declaring statement's implicit autocommit transaction ends.
                async with conn.cursor(name='redshift_run_query', withhold=True) as cur:
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
            log.warning(f'run_query error: {e}')
            return json.dumps({'error': str(e)})
