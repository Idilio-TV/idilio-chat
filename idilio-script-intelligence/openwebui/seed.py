"""Registers idilio-script-intelligence -- as a native OpenWebUI Skill, plus
its Tools and Knowledge files -- against a running OpenWebUI instance via
its REST API, and attaches all three directly to a base model (default:
gpt-5.6-luna).

Deliberately does NOT create a separate selectable model preset. The point
of using OpenWebUI's Skill object (its own DB table + the `view_skill`
builtin + the <available_skills> manifest OpenWebUI injects per-model,
verified in backend/open_webui/utils/middleware.py) is that a skill loads
contextually -- like a Claude Code skill -- instead of being an always-on
system prompt you have to pick a special model to get. Attaching it to
gpt-5.6-luna's own meta.skillIds means: select gpt-5.6-luna like normal,
and the skill becomes available whenever its description matches what
you're asking for.

Idempotent-ish: re-running updates existing tools/knowledge/skill rather
than erroring on "already exists", so this is safe to re-run after editing
a Tool file or system_prompt.md.

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

# Not vendored here (third-party code -- see openwebui/README.md's
# "Optional companion" section for the install link and the review that
# was done before installing it). system_prompt.md's "Como hacer
# preguntas" section assumes this is attached: every question in the
# skill goes through it instead of plain text. If it's not installed yet,
# attach_to_base_model() skips it and warns instead of failing.
INTERACTIVE_QUESTION_TOOL_ID = 'ask_user_question'

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


def seed_skill(session: requests.Session, base_url: str) -> None:
    content = (HERE / 'system_prompt.md').read_text(encoding='utf-8')
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
        raise RuntimeError(
            f"base model '{base_model_id}' not found in OpenWebUI's model list "
            f'({resp.status_code}) -- it must exist as a model (even with no '
            'params.system override) before you can attach tools/knowledge/skills '
            'to it. Pick a model from Admin Settings -> Models, or create a '
            'zero-config entry for it first.'
        )
    model = resp.json()
    meta = model.get('meta') or {}

    tool_ids = set(meta.get('toolIds') or [])
    tool_ids.update(t_id for t_id, _ in TOOL_FILES)

    installed_tool_ids = {t['id'] for t in session.get(f'{base_url}/api/v1/tools/').json()}
    if INTERACTIVE_QUESTION_TOOL_ID in installed_tool_ids:
        tool_ids.add(INTERACTIVE_QUESTION_TOOL_ID)
    else:
        print(f"WARNING: '{INTERACTIVE_QUESTION_TOOL_ID}' isn't installed -- the skill's "
              'questions will fall back to plain text instead of the interactive picker. '
              'See openwebui/README.md, "Optional companion", to install it.')

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
    }
    r = session.post(f'{base_url}/api/v1/models/model/update', json=payload)
    if not r.ok:
        raise RuntimeError(f'failed to update base model {base_model_id}: {r.status_code} {r.text}')
    print(f'attached to {base_model_id}: toolIds={meta["toolIds"]}, '
          f'knowledge={[k["name"] for k in meta["knowledge"]]}, skillIds={meta["skillIds"]}')


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
    parser.add_argument(
        '--base-model-id',
        default='gpt-5.6-luna',
        help='Existing model to attach the skill/tools/knowledge to directly '
        '(no separate selectable model gets created).',
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip('/')
    session = requests.Session()

    authenticate(session, base_url, args.email, args.password)
    check_subagents_enabled(session, base_url)
    seed_tools(session, base_url)
    knowledge_id = get_or_create_knowledge(session, base_url)
    seed_knowledge_files(session, base_url, knowledge_id)
    seed_skill(session, base_url)
    attach_to_base_model(session, base_url, args.base_model_id, knowledge_id)

    print(f'\nDone. Select "{args.base_model_id}" like any other model in the '
          'chat UI -- the skill loads contextually when what you ask for '
          'matches its description, no separate model to pick.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
