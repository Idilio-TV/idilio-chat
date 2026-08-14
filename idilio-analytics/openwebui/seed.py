"""Bootstraps idilio-analytics against a running OpenWebUI instance via its
REST API: registers the Redshift Analytics Tool, the Idilio Dashboard
Reference Tool (live GitHub access to idilio-dashboard -- deliberately NOT a
static knowledge-file snapshot, since that repo changes too often for a
cached copy to stay trustworthy), and the Idilio Analytics Skill, then
attaches all three to a base model -- same pattern as
idilio-script-intelligence/openwebui/seed.py, just for the analytics/
Redshift domain instead of script writing. Instance-wide settings
(ENABLE_SUBAGENTS, the OpenAI Responses API switch, and disabling every
model but the active one) are handled by that other seed.py -- this script
only touches its own Tools/Skill and their attachment to base_model_id, so
running both is safe and non-conflicting.

Idempotent-ish: re-running updates the existing tools/skill rather than
erroring on "already exists", so this is safe to re-run after editing
tools/*.py or SKILL.md.

Usage:
    python seed.py --base-url http://localhost:8080 \
        --email admin@idilio.tv --password '...' \
        --base-model-id gpt-5.6-luna

If the instance has no users yet, the given email/password signs up as the
first user (which OpenWebUI makes an admin automatically). If a user with
that email already exists, signs in instead.

Requires: requests.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
TOOLS_DIR = HERE / 'tools'

TOOL_FILES = [
    ('redshift', 'Redshift Analytics'),
    ('dashboard_reference', 'Idilio Dashboard Reference'),
]

SKILL_ID = 'idilio-analytics'
SKILL_NAME = 'Idilio Analytics'
SKILL_DESCRIPTION = (
    'Use when someone asks an ad-hoc question about a company-wide metric (revenue, MRR, '
    'subscribers, DAU/MAU, retention, churn, active users) or wants a number pulled from '
    'the Redshift data warehouse -- ensures the answer matches the company\'s existing '
    'metric definitions instead of an improvised methodology.'
)


def authenticate(session: requests.Session, base_url: str, email: str, password: str) -> None:
    signin = session.post(
        f'{base_url}/api/v1/auths/signin', json={'email': email, 'password': password}
    )
    if signin.ok:
        print(f'signed in as {email}')
        return

    display_name = email.split('@', 1)[0].replace('.', ' ').title()
    signup = session.post(
        f'{base_url}/api/v1/auths/signup',
        json={'name': display_name, 'email': email, 'password': password},
    )
    if not signup.ok:
        raise RuntimeError(
            f'could not sign in or sign up ({signin.status_code}, then {signup.status_code}): '
            f'{signup.text}'
        )
    print(f'signed up as {email} (first user -> admin)')


def seed_tools(session: requests.Session, base_url: str) -> None:
    existing = {t['id']: t for t in session.get(f'{base_url}/api/v1/tools/').json()}
    for filename, display_name in TOOL_FILES:
        content = (TOOLS_DIR / f'{filename}.py').read_text(encoding='utf-8')
        tool_id = filename  # must be a valid Python identifier per the API
        if tool_id in existing:
            resp = session.post(
                f'{base_url}/api/v1/tools/id/{tool_id}/update',
                json={'id': tool_id, 'name': display_name, 'content': content, 'meta': {}},
            )
            action = 'updated'
        else:
            resp = session.post(
                f'{base_url}/api/v1/tools/create',
                json={'id': tool_id, 'name': display_name, 'content': content, 'meta': {}},
            )
            action = 'created'
        if not resp.ok:
            raise RuntimeError(f'failed to {action[:-1]} tool {tool_id}: {resp.status_code} {resp.text}')
        print(f'{action} tool: {tool_id}')


def seed_skill(session: requests.Session, base_url: str) -> None:
    content = (HERE / 'SKILL.md').read_text(encoding='utf-8')
    payload = {
        'id': SKILL_ID,
        'name': SKILL_NAME,
        'description': SKILL_DESCRIPTION,
        'content': content,
        'is_active': True,
    }
    existing = session.get(f'{base_url}/api/v1/skills/id/{SKILL_ID}')
    if existing.ok:
        resp = session.post(f'{base_url}/api/v1/skills/id/{SKILL_ID}/update', json=payload)
        action = 'updated'
    else:
        resp = session.post(f'{base_url}/api/v1/skills/create', json=payload)
        action = 'created'
    if not resp.ok:
        raise RuntimeError(f'failed to {action[:-1]} skill {SKILL_ID}: {resp.status_code} {resp.text}')
    print(f'{action} skill: {SKILL_ID}')


def attach_to_base_model(session: requests.Session, base_url: str, base_model_id: str) -> None:
    """Attach the tools and the skill directly to base_model_id's own meta
    -- merges into whatever's already there (e.g. idilio-script-intelligence's
    own attachments) instead of overwriting."""
    resp = session.get(f'{base_url}/api/v1/models/model?id={base_model_id}')
    if not resp.ok:
        live_models = session.get(f'{base_url}/api/models')
        live_ids = {m['id'] for m in live_models.json().get('data', [])} if live_models.ok else set()
        if base_model_id not in live_ids:
            raise RuntimeError(
                f"base model '{base_model_id}' isn't offered by any configured "
                f'connection ({len(live_ids)} models available) -- check the '
                'connection/API key before seeding.'
            )
        create_resp = session.post(
            f'{base_url}/api/v1/models/create',
            json={
                'id': base_model_id,
                'base_model_id': None,
                'name': base_model_id,
                'meta': {},
                'params': {},
                'access_grants': [],
            },
        )
        if not create_resp.ok:
            raise RuntimeError(
                f'failed to create model entry for {base_model_id}: '
                f'{create_resp.status_code} {create_resp.text}'
            )
        print(f'created model entry: {base_model_id}')
        resp = session.get(f'{base_url}/api/v1/models/model?id={base_model_id}')
        if not resp.ok:
            raise RuntimeError(
                f"created model entry for '{base_model_id}' but couldn't read it back "
                f'({resp.status_code}) -- something is wrong beyond a missing entry.'
            )
    model = resp.json()
    meta = model.get('meta') or {}

    tool_ids = set(meta.get('toolIds') or [])
    tool_ids.update(t_id for t_id, _ in TOOL_FILES)
    meta['toolIds'] = sorted(tool_ids)

    skill_ids = set(meta.get('skillIds') or [])
    skill_ids.add(SKILL_ID)
    meta['skillIds'] = sorted(skill_ids)

    payload = {
        'id': model['id'],
        'base_model_id': model.get('base_model_id'),
        'name': model['name'],
        'meta': meta,
        'params': model.get('params') or {},
        'access_grants': model.get('access_grants') or [],
        'is_active': model.get('is_active', True),
    }
    r = session.post(f'{base_url}/api/v1/models/model/update', json=payload)
    if not r.ok:
        raise RuntimeError(f'failed to update base model {base_model_id}: {r.status_code} {r.text}')
    print(f'attached to {base_model_id}: toolIds={meta["toolIds"]}, skillIds={meta["skillIds"]}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://localhost:8080')
    parser.add_argument('--email', required=True)
    parser.add_argument('--password', required=True)
    parser.add_argument(
        '--base-model-id',
        default='gpt-5.6-luna',
        help='Comma-separated list of existing models to attach the tools/skill '
        'to directly. Every model listed gets the exact same attachment.',
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip('/')
    base_model_ids = [m.strip() for m in args.base_model_id.split(',') if m.strip()]
    session = requests.Session()

    authenticate(session, base_url, args.email, args.password)
    seed_tools(session, base_url)
    seed_skill(session, base_url)
    for base_model_id in base_model_ids:
        attach_to_base_model(session, base_url, base_model_id)

    print(f'\nDone. {SKILL_NAME} is attached to {base_model_ids} -- the skill loads '
          'contextually when what you ask for matches its description, no separate '
          'model to pick.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
