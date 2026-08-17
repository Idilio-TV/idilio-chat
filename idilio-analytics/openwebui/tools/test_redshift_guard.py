"""
Self-check for the Redshift read-only SQL guard.

Run directly: python3 test_redshift_guard.py
Plain asserts only -- no pytest required, though pytest would pick these up too.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from redshift import ReadOnlySQLError, _ensure_read_only_sql  # noqa: E402


def test_allows_plain_select():
    _ensure_read_only_sql('SELECT * FROM analytics_marts.stg_orders LIMIT 10')


def test_allows_select_with_update_like_identifier():
    _ensure_read_only_sql('SELECT updated_at FROM public.purchases WHERE updated_at > now()')


def test_allows_single_trailing_semicolon():
    _ensure_read_only_sql('SELECT 1;')


def test_blocks_insert():
    try:
        _ensure_read_only_sql('INSERT INTO public.foo VALUES (1)')
    except ReadOnlySQLError:
        pass
    else:
        raise AssertionError('expected ReadOnlySQLError for INSERT')


def test_blocks_drop_table():
    try:
        _ensure_read_only_sql('DROP TABLE public.purchases')
    except ReadOnlySQLError:
        pass
    else:
        raise AssertionError('expected ReadOnlySQLError for DROP TABLE')


def test_blocks_delete_case_insensitive():
    try:
        _ensure_read_only_sql('delete from public.purchases where id = 1')
    except ReadOnlySQLError:
        pass
    else:
        raise AssertionError('expected ReadOnlySQLError for lowercase delete')


def test_blocks_grant():
    try:
        _ensure_read_only_sql('GRANT SELECT ON public.purchases TO someone')
    except ReadOnlySQLError:
        pass
    else:
        raise AssertionError('expected ReadOnlySQLError for GRANT')


def test_blocks_select_into():
    try:
        _ensure_read_only_sql('SELECT * INTO new_table FROM public.purchases')
    except ReadOnlySQLError:
        pass
    else:
        raise AssertionError('expected ReadOnlySQLError for SELECT INTO')


def test_blocks_multiple_statements():
    try:
        _ensure_read_only_sql('SELECT 1; SELECT * FROM public.credit_cards')
    except ReadOnlySQLError:
        pass
    else:
        raise AssertionError('expected ReadOnlySQLError for stacked statements')


def test_blocks_analyze_prefix():
    try:
        _ensure_read_only_sql('ANALYZE SELECT * FROM public.credit_cards')
    except ReadOnlySQLError:
        pass
    else:
        raise AssertionError('expected ReadOnlySQLError for ANALYZE prefix')


if __name__ == '__main__':
    test_allows_plain_select()
    test_allows_select_with_update_like_identifier()
    test_allows_single_trailing_semicolon()
    test_blocks_insert()
    test_blocks_drop_table()
    test_blocks_delete_case_insensitive()
    test_blocks_grant()
    test_blocks_select_into()
    test_blocks_multiple_statements()
    test_blocks_analyze_prefix()
    print('OK: all redshift guard checks passed')
