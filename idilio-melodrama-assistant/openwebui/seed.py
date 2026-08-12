"""Registers the idilio-script-intelligence Tools and Knowledge files
against a running OpenWebUI instance via its REST API.

Idempotent-ish: re-running updates existing tools/knowledge by name rather
than erroring on "already exists", so this is safe to re-run after editing
a Tool file.

Usage:
    python seed.py --base-url http://localhost:8080 \
        --email admin@idilio.tv --password '...'

If the instance has no users yet, the given email/password signs up as the
first user (which OpenWebUI makes an admin automatically). If a user with
that email already exists, signs in instead.

Requires: requests (stdlib http.client would work too, but requests keeps
this readable -- reuses whatever's already in this repo's Python env).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
TOOLS_DIR = HERE / 'tools'
KNOWLEDGE_DIR = HERE / 'knowledge'
KNOWLEDGE_NAME = 'Melodrama Script Intelligence'
KNOWLEDGE_DESCRIPTION = (
    'Referencia de la skill Melodrama Script Intelligence: teoria de '
    'Brooks, estructura de 12 pasos, guia de formato y rubrica de '
    'hook/cliffhanger.'
)

TOOL_FILES = [
    ('melodrama_guion', 'Melodrama Guion'),
    ('melodrama_export_docx', 'Melodrama Export a DOCX'),
]


def authenticate(session: requests.Session, base_url: str, email: str, password: str) -> None:
    signin = session.post(
        f'{base_url}/api/v1/auths/signin', json={'email': email, 'password': password}
    )
    if signin.ok:
        print(f'signed in as {email}')
        return

    signup = session.post(
        f'{base_url}/api/v1/auths/signup',
        json={'name': 'Idilio Seed', 'email': email, 'password': password},
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


def get_or_create_knowledge(session: requests.Session, base_url: str) -> str:
    existing = session.get(f'{base_url}/api/v1/knowledge/').json()['items']
    for item in existing:
        if item['name'] == KNOWLEDGE_NAME:
            print(f"reusing knowledge collection: {item['id']}")
            return item['id']

    resp = session.post(
        f'{base_url}/api/v1/knowledge/create',
        json={'name': KNOWLEDGE_NAME, 'description': KNOWLEDGE_DESCRIPTION},
    )
    if not resp.ok:
        raise RuntimeError(f'failed to create knowledge collection: {resp.status_code} {resp.text}')
    knowledge_id = resp.json()['id']
    print(f'created knowledge collection: {knowledge_id}')
    return knowledge_id


def seed_knowledge_files(session: requests.Session, base_url: str, knowledge_id: str) -> None:
    existing_files = session.get(f'{base_url}/api/v1/knowledge/{knowledge_id}/files').json()['items']
    already_attached = {f['filename'] for f in existing_files}

    for path in sorted(KNOWLEDGE_DIR.glob('*')):
        if not path.is_file():
            continue
        if path.name in already_attached:
            print(f'already attached, skipping: {path.name}')
            continue
        with open(path, 'rb') as f:
            upload = session.post(f'{base_url}/api/v1/files/', files={'file': (path.name, f)})
        if not upload.ok:
            raise RuntimeError(f'failed to upload {path.name}: {upload.status_code} {upload.text}')
        file_id = upload.json()['id']

        attach = session.post(
            f'{base_url}/api/v1/knowledge/{knowledge_id}/file/add',
            json={'file_id': file_id},
        )
        if not attach.ok:
            raise RuntimeError(f'failed to attach {path.name} to knowledge: {attach.status_code} {attach.text}')
        print(f'uploaded + attached: {path.name}')


def check_subagents_enabled(session: requests.Session, base_url: str) -> None:
    # Parallel alternatives (Etapa 1/2/5/6) rely on OpenWebUI's builtin
    # delegate_task -- the middleware runs multiple delegate_task calls in
    # one turn through asyncio.gather (a real parallel fan-out, unlike
    # every other tool call, which it awaits one at a time). That tool is
    # only exposed to a chat when ENABLE_SUBAGENTS is on.
    resp = session.get(f'{base_url}/api/v1/configs/subagents')
    if not resp.ok:
        print(f'WARNING: could not read subagents config ({resp.status_code}) -- '
              'skipping the check. Confirm ENABLE_SUBAGENTS manually if alternatives '
              "don't come back as real parallel calls.")
        return
    enabled = resp.json().get('ENABLE_SUBAGENTS')
    if enabled:
        print('subagents: already enabled (delegate_task available)')
    else:
        print('WARNING: ENABLE_SUBAGENTS is off on this instance. The system prompt '
              'assumes delegate_task is available for parallel alternatives -- enable it '
              'in Admin Settings -> Subagents, or POST {"ENABLE_SUBAGENTS": true, ...} to '
              '/api/v1/configs/subagents, before using this assistant.')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://localhost:8080')
    parser.add_argument('--email', required=True)
    parser.add_argument('--password', required=True)
    args = parser.parse_args()

    base_url = args.base_url.rstrip('/')
    session = requests.Session()

    authenticate(session, base_url, args.email, args.password)
    check_subagents_enabled(session, base_url)
    seed_tools(session, base_url)
    knowledge_id = get_or_create_knowledge(session, base_url)
    seed_knowledge_files(session, base_url, knowledge_id)

    print('\nDone. In the OpenWebUI admin UI:')
    print('1. Workspace -> Models -> create a model preset.')
    print(f'2. Paste {HERE / "system_prompt.md"} as its System Prompt.')
    print('3. Attach the 2 melodrama_* tools and the "Melodrama Script')
    print('   Intelligence" knowledge collection to that model.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
