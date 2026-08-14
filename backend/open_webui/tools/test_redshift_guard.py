"""
Self-check for the Redshift read-only SQL guard.

Run directly: python -m open_webui.tools.test_redshift_guard
Plain asserts only — no pytest required, though pytest would pick these up too.
"""

from open_webui.tools.redshift import ReadOnlySQLError, _ensure_read_only_sql


def test_allows_plain_select():
    _ensure_read_only_sql('SELECT * FROM analytics_marts.stg_orders LIMIT 10')


def test_allows_select_with_update_like_identifier():
    _ensure_read_only_sql('SELECT updated_at FROM public.purchases WHERE updated_at > now()')


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


if __name__ == '__main__':
    test_allows_plain_select()
    test_allows_select_with_update_like_identifier()
    test_blocks_insert()
    test_blocks_drop_table()
    test_blocks_delete_case_insensitive()
    test_blocks_grant()
    test_blocks_select_into()
    print('OK: all redshift guard checks passed')
