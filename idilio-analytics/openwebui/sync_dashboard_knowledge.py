"""Keeps the "Idilio Dashboard Reference" Knowledge collection in OpenWebUI
current with a curated set of files from the idilio-dashboard repo. Runs
continuously (the idilio-dashboard-sync service in docker-compose.yaml):
every SYNC_INTERVAL_SECONDS, re-reads CURATED_FILES from the bind-mounted
repo checkout and replaces the collection's files with the current content.

Deliberately a full remove-then-reupload each run rather than a checksum
diff -- CURATED_FILES is a handful of small files, so re-embedding all of
them every interval is negligible cost, and "reconstruct from scratch" has
no diff-bug surface. (OpenWebUI does have a purpose-built manifest-diff
sync API at /{id}/sync/diff -- worth switching to if CURATED_FILES grows
into the hundreds and re-embedding everything every run becomes wasteful.)

Auth reuses DEPLOY_ADMIN_EMAIL/DEPLOY_ADMIN_PASSWORD, same as seed.py --
these are the same admin credentials deploy.sh already establishes.

Env vars:
    OPENWEBUI_BASE_URL       default: http://open-webui:8080 (docker network)
    DEPLOY_ADMIN_EMAIL       required
    DEPLOY_ADMIN_PASSWORD    required
    MOUNT_PATH                default: /mnt/idilio-dashboard
    SYNC_INTERVAL_SECONDS      default: 3600
"""
from __future__ import annotations

import os
import sys
import time
import traceback
from pathlib import Path

import requests

KNOWLEDGE_NAME = 'Idilio Dashboard Reference'
KNOWLEDGE_DESCRIPTION = (
    'Reference material for company-wide metrics (revenue, MRR, retention, active users, '
    'DAU/MAU) synced periodically from the idilio-dashboard repo -- kept current by '
    'sync_dashboard_knowledge.py, not a one-time snapshot.'
)

# Relative paths within the idilio-dashboard repo. Uploaded under a flattened
# filename (path with "/" replaced by "__") so they don't collide and stay
# identifiable in the Knowledge UI.
CURATED_FILES = [
    'CLAUDE.md',
    'api/chat/prompt_assets/canonical_rules.md',
    'api/metrics/handlers.py',
    'api/metrics/handlers_campaigns.py',
    'api/metrics/handlers_shows_roas.py',
    'api/metrics/handlers_unit_economics.py',
]


def authenticate(session: requests.Session, base_url: str, email: str, password: str) -> None:
    signin = session.post(f'{base_url}/api/v1/auths/signin', json={'email': email, 'password': password})
    if not signin.ok:
        raise RuntimeError(f'failed to sign in as {email}: {signin.status_code} {signin.text}')


def get_or_create_knowledge(session: requests.Session, base_url: str) -> str:
    existing = session.get(f'{base_url}/api/v1/knowledge/').json()['items']
    for item in existing:
        if item['name'] == KNOWLEDGE_NAME:
            return item['id']

    resp = session.post(
        f'{base_url}/api/v1/knowledge/create',
        json={'name': KNOWLEDGE_NAME, 'description': KNOWLEDGE_DESCRIPTION},
    )
    if not resp.ok:
        raise RuntimeError(f'failed to create knowledge collection: {resp.status_code} {resp.text}')
    return resp.json()['id']


def clear_existing_files(session: requests.Session, base_url: str, knowledge_id: str) -> None:
    files = session.get(f'{base_url}/api/v1/knowledge/{knowledge_id}/files').json()['items']
    for f in files:
        resp = session.post(f'{base_url}/api/v1/knowledge/{knowledge_id}/file/remove', json={'file_id': f['id']})
        if not resp.ok:
            raise RuntimeError(f"failed to remove stale file {f['filename']}: {resp.status_code} {resp.text}")


def upload_and_attach(session: requests.Session, base_url: str, knowledge_id: str, filename: str, content: bytes) -> None:
    upload = session.post(f'{base_url}/api/v1/files/', files={'file': (filename, content)})
    if not upload.ok:
        raise RuntimeError(f'failed to upload {filename}: {upload.status_code} {upload.text}')
    file_id = upload.json()['id']

    # Same OpenWebUI upload/attach race documented in
    # idilio-script-intelligence/openwebui/seed.py -- retry on the two known
    # transient error strings, trusting the collection's file list as ground
    # truth over the HTTP response.
    RACE_MARKERS = ('content provided is empty', 'duplicate content detected')
    last_error = None
    for attempt in range(1, 4):
        attach = session.post(f'{base_url}/api/v1/knowledge/{knowledge_id}/file/add', json={'file_id': file_id})
        if attach.ok:
            return
        last_error = f'{attach.status_code} {attach.text}'
        if not any(marker in attach.text.lower() for marker in RACE_MARKERS):
            break
        time.sleep(attempt * 2)
        current = session.get(f'{base_url}/api/v1/knowledge/{knowledge_id}/files').json()['items']
        if any(f['filename'] == filename for f in current):
            return
    raise RuntimeError(f'failed to attach {filename} to knowledge: {last_error}')


def sync_once(base_url: str, email: str, password: str, mount_path: str) -> None:
    root = Path(mount_path)
    if not root.is_dir():
        raise RuntimeError(f'{mount_path} is not mounted -- check IDILIO_DASHBOARD_PATH on the host.')

    session = requests.Session()
    authenticate(session, base_url, email, password)
    knowledge_id = get_or_create_knowledge(session, base_url)
    clear_existing_files(session, base_url, knowledge_id)

    synced = 0
    for rel_path in CURATED_FILES:
        source = root / rel_path
        if not source.is_file():
            print(f'skipping missing file: {rel_path}', file=sys.stderr)
            continue
        filename = rel_path.replace('/', '__')
        upload_and_attach(session, base_url, knowledge_id, filename, source.read_bytes())
        synced += 1

    print(f'synced {synced}/{len(CURATED_FILES)} files into "{KNOWLEDGE_NAME}"')


def main() -> int:
    base_url = os.environ.get('OPENWEBUI_BASE_URL', 'http://open-webui:8080').rstrip('/')
    email = os.environ['DEPLOY_ADMIN_EMAIL']
    password = os.environ['DEPLOY_ADMIN_PASSWORD']
    mount_path = os.environ.get('MOUNT_PATH', '/mnt/idilio-dashboard')
    interval = int(os.environ.get('SYNC_INTERVAL_SECONDS', '3600'))

    FAILURE_RETRY_SECONDS = 60

    while True:
        try:
            sync_once(base_url, email, password, mount_path)
            time.sleep(interval)
        except Exception:
            print('sync failed, retrying sooner than the normal interval:', file=sys.stderr)
            traceback.print_exc()
            time.sleep(FAILURE_RETRY_SECONDS)


if __name__ == '__main__':
    sys.exit(main())
