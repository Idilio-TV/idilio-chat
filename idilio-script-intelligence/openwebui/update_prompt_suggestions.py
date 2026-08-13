"""Pushes backend/open_webui/config.py's DEFAULT_PROMPT_SUGGESTIONS to a
running instance's ui.prompt_suggestions config, via the same endpoint
Admin Settings -> Default Prompt Suggestions itself uses.

Needed because that value only seeds the DB on a fresh instance --
existing DB values take precedence over code changes (see
models/config.py's seed_defaults), so editing config.py alone does
nothing for an instance that's already booted once. Run this once after
a deploy that changes the defaults, same as you'd click Save in Admin
Settings by hand.

Usage:
    python3 update_prompt_suggestions.py --base-url http://localhost:8080

DEPLOY_ADMIN_EMAIL / DEPLOY_ADMIN_PASSWORD are read from the environment
(same vars deploy.sh sources from .env) unless passed explicitly via
--email/--password.
"""
from __future__ import annotations

import argparse
import ast
import os
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PY = REPO_ROOT / 'backend' / 'open_webui' / 'config.py'


def parse_default_suggestions() -> list[dict]:
    """Extract the literal list assigned inside config.py's `if
    default_prompt_suggestions == []:` block, so this can never drift from
    the actual source of truth by hand-copying it elsewhere."""
    src = CONFIG_PY.read_text(encoding='utf-8')
    anchor = src.index('if default_prompt_suggestions == []:')
    start = src.index('[', src.index('default_prompt_suggestions = [', anchor))
    depth = 0
    end = start
    for i, c in enumerate(src[start:], start):
        if c == '[':
            depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    # ast.literal_eval, not eval: this only ever needs to parse a literal
    # list-of-dicts-of-strings, never execute anything.
    return ast.literal_eval(src[start:end])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://localhost:8080')
    parser.add_argument('--email', default=os.environ.get('DEPLOY_ADMIN_EMAIL'))
    parser.add_argument('--password', default=os.environ.get('DEPLOY_ADMIN_PASSWORD'))
    args = parser.parse_args()

    if not args.email or not args.password:
        parser.error(
            '--email/--password required (or set DEPLOY_ADMIN_EMAIL/DEPLOY_ADMIN_PASSWORD, '
            'same as deploy.sh)'
        )

    base_url = args.base_url.rstrip('/')
    suggestions = parse_default_suggestions()
    print(f'{len(suggestions)} suggestions parsed from {CONFIG_PY.relative_to(REPO_ROOT)}')

    session = requests.Session()
    signin = session.post(
        f'{base_url}/api/v1/auths/signin', json={'email': args.email, 'password': args.password}
    )
    if not signin.ok:
        raise RuntimeError(f'sign-in failed: {signin.status_code} {signin.text}')

    resp = session.post(f'{base_url}/api/v1/configs/suggestions', json={'suggestions': suggestions})
    if not resp.ok:
        raise RuntimeError(f'failed to update suggestions: {resp.status_code} {resp.text}')

    titles = [s['title'][0] for s in resp.json()]
    print(f'updated ui.prompt_suggestions ({len(titles)}): {titles}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
