"""Bootstraps idilio-script-intelligence against a running OpenWebUI
instance via its REST API: registers the Skill, Tools, and Knowledge
files, attaches all three to a base model (default: gpt-5.6-luna), and
applies the two admin-panel settings this setup depends on
(ENABLE_SUBAGENTS, and the OpenAI connection's Responses API switch) --
everything needed to go from a fresh instance to a working assistant in
one run, except secrets (OPENAI_API_KEY etc., which live in .env / the
connection's own config, never in this script or the repo).

Deliberately does NOT create a separate selectable model preset. The point
of using OpenWebUI's Skill object (its own DB table + the `view_skill`
builtin + the <available_skills> manifest OpenWebUI injects per-model,
verified in backend/open_webui/utils/middleware.py) is that a skill loads
contextually -- like a Claude Code skill -- instead of being an always-on
system prompt you have to pick a special model to get. Attaching it to
gpt-5.6-luna's own meta.skillIds means: select gpt-5.6-luna like normal,
and the skill becomes available whenever its description matches what
you're asking for.

Idempotent-ish: re-running updates existing tools/knowledge/skill/settings
rather than erroring on "already exists" or clobbering unrelated config,
so this is safe to re-run after editing a Tool file or SKILL.md, or just
to confirm an instance is fully configured.

Usage:
    python seed.py --base-url http://localhost:8080 \
        --email admin@idilio.tv --password '...' \
        --base-model-id gpt-5.6-luna

If the instance has no users yet, the given email/password signs up as the
first user (which OpenWebUI makes an admin automatically). If a user with
that email already exists, signs in instead.

Requires: requests (stdlib http.client would work too, but requests keeps
this readable -- reuses whatever's already in this repo's Python env).
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
TOOLS_DIR = HERE / 'tools'
KNOWLEDGE_DIR = HERE / 'knowledge'
KNOWLEDGE_NAME = 'Idilio Script Intelligence'
KNOWLEDGE_DESCRIPTION = (
    'Referencia de la skill Idilio Script Intelligence: teoria de '
    'Brooks, estructura de 12 pasos, guia de formato y rubrica de '
    'hook/cliffhanger.'
)

TOOL_FILES = [
    ('script_guion', 'Script Guion'),
    ('script_export_docx', 'Script Export a DOCX'),
]

SKILL_ID = 'idilio-script-intelligence'
SKILL_NAME = 'Idilio Script Intelligence'
# Same trigger description as the Claude Code plugin's SKILL.md frontmatter,
# kept in sync by hand -- this is what OpenWebUI shows the model in the
# lightweight <available_skills> manifest to decide whether to load the
# full content via view_skill().
SKILL_DESCRIPTION = (
    "Use when a libretista is developing or writing a melodrama script for "
    "an Idilio vertical short-format show -- from a bare idea through a "
    "finished, chapter-by-chapter guion. Acts as a writing partner: asks "
    "one question at a time, dispatches parallel sub-agents for "
    "character/premise, argumento/hook, and twist/climax alternatives, and "
    "runs a scored hook/cliffhanger review (grounded in Peter Brooks' "
    "melodrama theory and Idilio's real hook_score/cliffhanger_score "
    "definitions) before a chapter ships. Trigger on requests like 'quiero "
    "escribir un melodrama', 'ayudame con este guion/libreto', 'dame el "
    "argumento de este show', 'busquemos el mejor personaje para este "
    "universo', 'revisa el cliffhanger/hook del capitulo N', or any request "
    "to develop character, plot, structure, twists, or chapters for a "
    "vertical melodrama."
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

        # OpenWebUI's /file/add response is unreliable here: there's a race
        # between upload finishing and the file being flushed to disk, so
        # an immediate attach can get a spurious "content provided is
        # empty" 400 -- but the background embedding job it kicked off
        # keeps running and can still complete successfully seconds later
        # (confirmed against a real deploy: same file, same loader call,
        # extracts perfectly when re-run manually right after). Sometimes
        # that background completion then makes the NEXT attempt 400 with
        # "Duplicate content detected" instead, because the content is
        # already indexed under this file_id -- also not a real failure.
        # Rather than trust the HTTP response, check the knowledge
        # collection's actual file list after each attempt and treat
        # presence there as ground truth.
        RACE_MARKERS = ('content provided is empty', 'duplicate content detected')
        attached = False
        last_error = None
        for attempt in range(1, 4):
            attach = session.post(
                f'{base_url}/api/v1/knowledge/{knowledge_id}/file/add',
                json={'file_id': file_id},
            )
            if attach.ok:
                attached = True
                break

            last_error = f'{attach.status_code} {attach.text}'
            if not any(marker in attach.text.lower() for marker in RACE_MARKERS):
                break  # a different failure -- don't mask it with retries

            time.sleep(attempt * 2)
            current = session.get(f'{base_url}/api/v1/knowledge/{knowledge_id}/files').json()['items']
            if any(f['filename'] == path.name for f in current):
                attached = True
                last_error = None
                break
            print(f'  attach attempt {attempt}/3 hit a known OpenWebUI race, retrying...')

        if not attached:
            raise RuntimeError(f'failed to attach {path.name} to knowledge: {last_error}')
        print(f'uploaded + attached: {path.name}')


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


def attach_to_base_model(
    session: requests.Session, base_url: str, base_model_id: str, knowledge_id: str
) -> None:
    """Attach the 2 tools, the knowledge collection, and the skill directly
    to base_model_id's own meta -- no separate model preset. Merges into
    whatever's already there instead of overwriting, so this is safe to
    re-run alongside other things attached to the same model by hand."""
    resp = session.get(f'{base_url}/api/v1/models/model?id={base_model_id}')
    if not resp.ok:
        # No persisted Model row yet for this id -- distinct from whether the
        # connection can actually serve it (that's /api/models, the live
        # upstream list; this is the separate DB table a Model's own
        # meta/params/tool attachments live on). Create a bare entry rather
        # than requiring an admin to click through Settings -> Models first.
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

    knowledge = meta.get('knowledge') or []
    if not any(k.get('id') == knowledge_id for k in knowledge):
        knowledge.append({'id': knowledge_id, 'name': KNOWLEDGE_NAME, 'type': 'collection'})
    meta['knowledge'] = knowledge

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
        # ModelForm defaults is_active to True when the key is omitted, which
        # would silently re-enable a model ensure_only_active() disabled on a
        # prior run -- carry the current value forward instead.
        'is_active': model.get('is_active', True),
    }
    r = session.post(f'{base_url}/api/v1/models/model/update', json=payload)
    if not r.ok:
        raise RuntimeError(f'failed to update base model {base_model_id}: {r.status_code} {r.text}')
    print(f'attached to {base_model_id}: toolIds={meta["toolIds"]}, '
          f'knowledge={[k["name"] for k in meta["knowledge"]]}, skillIds={meta["skillIds"]}')


def ensure_only_active(session: requests.Session, base_url: str, active_model_id: str) -> None:
    """Disable every model except active_model_id, so only one is
    selectable in the chat UI -- not just gpt-5.6-luna/terra/sol, but every
    raw upstream model the connection reports (gpt-4, gpt-5.x, etc., ~100+
    on a real OpenAI connection). Most of those have no Models-table row at
    all until something overrides them (confirmed: POST .../model/toggle
    on a live-only id 401s, "model not found" -- the toggle endpoint only
    flips an *existing* row), so disabling one for the first time means
    creating a disabled override row directly rather than toggling.
    Iterates /api/models (the live merged list, same one the chat picker
    and admin Models page use) against /api/v1/models/base (every existing
    base-style override row, id -> base_model_id None) to decide, per live
    id, whether to leave it alone, toggle an existing row, or create one.
    Idempotent: skips anything already in the right state."""
    resp = session.get(f'{base_url}/api/models')
    if not resp.ok:
        raise RuntimeError(f'failed to list live models: {resp.status_code} {resp.text}')
    live_ids = [m['id'] for m in resp.json().get('data', [])]

    existing_resp = session.get(f'{base_url}/api/v1/models/base')
    if not existing_resp.ok:
        raise RuntimeError(
            f'failed to list existing model overrides: {existing_resp.status_code} {existing_resp.text}'
        )
    existing = {m['id']: m for m in existing_resp.json()}

    changed = 0
    for model_id in live_ids:
        want_active = model_id == active_model_id
        model = existing.get(model_id)
        if model:
            if model.get('is_active') == want_active:
                continue
            r = session.post(f'{base_url}/api/v1/models/model/toggle', params={'id': model_id})
            if not r.ok:
                raise RuntimeError(f'failed to toggle is_active for {model_id}: {r.status_code} {r.text}')
        elif not want_active:
            r = session.post(
                f'{base_url}/api/v1/models/create',
                json={
                    'id': model_id,
                    'base_model_id': None,
                    'name': model_id,
                    'meta': {},
                    'params': {},
                    'access_grants': [],
                    'is_active': False,
                },
            )
            if not r.ok:
                raise RuntimeError(f'failed to disable {model_id}: {r.status_code} {r.text}')
        else:
            continue  # want_active with no row -- attach_to_base_model already created/activated this one
        print(f'{model_id}: is_active -> {want_active}')
        changed += 1
    print(f'is_active: only {active_model_id} enabled ({changed} of {len(live_ids)} live models changed)')


OPENAI_RESPONSES_API_HOST = 'api.openai.com'


def ensure_subagents_enabled(session: requests.Session, base_url: str) -> None:
    """Turn on ENABLE_SUBAGENTS if it's off, so delegate_task (real parallel
    alternatives via the asyncio.gather fast-path in middleware.py) is
    actually available -- without this, the model can still call
    delegate_task, but the fan-out never triggers. The POST endpoint
    requires the full SubagentsConfigForm, not a partial patch, so this
    always GETs current values first and only flips the one field, leaving
    background_enabled/max_concurrent/etc. exactly as an admin set them."""
    resp = session.get(f'{base_url}/api/v1/configs/subagents')
    if not resp.ok:
        print(f'WARNING: could not read subagents config ({resp.status_code}) -- '
              'skipping. Confirm ENABLE_SUBAGENTS manually if alternatives '
              "don't come back as real parallel calls.")
        return
    config = resp.json()
    if config.get('ENABLE_SUBAGENTS'):
        print('subagents: already enabled (delegate_task available)')
        return
    config['ENABLE_SUBAGENTS'] = True
    r = session.post(f'{base_url}/api/v1/configs/subagents', json=config)
    if not r.ok:
        raise RuntimeError(f'failed to enable subagents: {r.status_code} {r.text}')
    print('subagents: enabled ENABLE_SUBAGENTS (was off)')


def ensure_responses_api(
    session: requests.Session, base_url: str, connection_host: str = OPENAI_RESPONSES_API_HOST
) -> None:
    """Switch the OpenAI-compatible connection matching connection_host to
    the Responses API (api_type: "responses") instead of Chat Completions
    -- required for gpt-5.6-luna/terra to use reasoning_effort and function
    tools in the same call (Chat Completions rejects that combination for
    this model family). This is connection-wide: every model routed
    through that connection picks it up, not just gpt-5.6-luna -- that's
    an intentional, already-confirmed tradeoff for this shared connection,
    not something to silently redo per model."""
    resp = session.get(f'{base_url}/openai/config')
    if not resp.ok:
        print(f'WARNING: could not read OpenAI connections config ({resp.status_code}) -- '
              'skipping. Set api_type to "responses" manually on the '
              f'{connection_host} connection in Admin Settings -> Connections '
              'if you see a "Function tools with reasoning_effort are not '
              'supported" error.')
        return
    config = resp.json()
    base_urls = config.get('OPENAI_API_BASE_URLS') or []
    idx = next((i for i, url in enumerate(base_urls) if connection_host in url), None)
    if idx is None:
        print(f'WARNING: no OpenAI connection matching "{connection_host}" found -- skipping.')
        return

    api_configs = config.get('OPENAI_API_CONFIGS') or {}
    conn_config = api_configs.get(str(idx)) or {}
    if conn_config.get('api_type') == 'responses':
        print(f'{connection_host} connection: already using the Responses API')
        return

    conn_config['api_type'] = 'responses'
    api_configs[str(idx)] = conn_config
    config['OPENAI_API_CONFIGS'] = api_configs

    r = session.post(f'{base_url}/openai/config/update', json=config)
    if not r.ok:
        raise RuntimeError(
            f'failed to switch {connection_host} to the Responses API: {r.status_code} {r.text}'
        )
    print(f'{connection_host} connection: switched to the Responses API '
          '(affects every model on this connection, not just gpt-5.6-luna)')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://localhost:8080')
    parser.add_argument('--email', required=True)
    parser.add_argument('--password', required=True)
    parser.add_argument(
        '--base-model-id',
        default='gpt-5.6-luna',
        help='Comma-separated list of existing models to attach the '
        'skill/tools/knowledge to directly (no separate selectable model '
        'gets created). Every model listed gets the exact same attachment '
        '-- there is no per-model variation.',
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip('/')
    base_model_ids = [m.strip() for m in args.base_model_id.split(',') if m.strip()]
    session = requests.Session()

    authenticate(session, base_url, args.email, args.password)
    ensure_subagents_enabled(session, base_url)
    ensure_responses_api(session, base_url)
    seed_tools(session, base_url)
    knowledge_id = get_or_create_knowledge(session, base_url)
    seed_knowledge_files(session, base_url, knowledge_id)
    seed_skill(session, base_url)
    for base_model_id in base_model_ids:
        attach_to_base_model(session, base_url, base_model_id, knowledge_id)

    active_model_id = next((m for m in base_model_ids if 'terra' in m), None)
    if active_model_id:
        ensure_only_active(session, base_url, active_model_id)
        print(f'\nDone. {active_model_id} is the only model visible anywhere in '
              'the chat UI -- the skill loads contextually when what you ask '
              'for matches its description, no separate model to pick.')
    else:
        print(
            f"WARNING: no model in {base_model_ids} contains 'terra' -- skipping "
            'is_active toggling, every model stays as it was.'
        )
        print(f'\nDone. Select any of {base_model_ids} like any other model in '
              'the chat UI -- the skill loads contextually when what you ask '
              'for matches its description, no separate model to pick.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
