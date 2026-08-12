# Idilio Script Intelligence — OpenWebUI

The most faithful port of the three platforms in this directory — unlike
the Claude Code plugin (via the `Agent` tool) and the ChatGPT bundle (no
real tools at all), OpenWebUI gives this assistant **real parallel
sub-agents, real file persistence, and a native contextual Skill** —
nothing to select, it loads itself when relevant.

## Setup

1. Bring up `idilio-chat` (`docker-compose up -d` from the repo root) and
   make sure a model is available (e.g. `docker exec ollama ollama pull
   <model>`, or configure an OpenAI-compatible connection in Admin
   Settings). It doesn't need to be a fresh/dedicated model — this attaches
   to a model you already use for other things.
2. Run the seed script:
   ```bash
   cd idilio-script-intelligence/openwebui
   python3 seed.py --base-url http://localhost:3000 \
       --email you@idilio.tv --password '...' \
       --base-model-id gpt-5.6-luna
   ```
   This registers the 2 custom tools (`script_guion`,
   `script_export_docx`), creates the "Idilio Script Intelligence"
   Knowledge collection, uploads the 3 reference `.md` files into it,
   registers `system_prompt.md`'s content as a native OpenWebUI **Skill**
   (see below), checks that subagents are enabled, and attaches the tools
   + knowledge + skill directly to `--base-model-id` (default
   `gpt-5.6-luna`) — merged into whatever's already attached there, not
   overwritten. Safe to re-run after editing a tool file or
   `system_prompt.md`.
3. That's it. Select `gpt-5.6-luna` (or whatever `--base-model-id` you
   used) like any other model in the chat UI. **There is no separate
   "Idilio Script Intelligence" model to pick** — the skill loads itself
   contextually when what you ask for matches its description (see "Native
   Skills" below), same model you'd use for anything else.
4. If `seed.py` warned that subagents are off: **Admin Settings →
   Subagents → Enable Subagents.** (On a fresh instance this defaults to
   off; enable once, server-wide.)

## Native Skills — why this isn't a model preset

This fork has its own first-class **Skill** object (`backend/open_webui/models/skills.py`
— its own DB table: `id`, `name`, `description`, `content`, separate from
Tools/Functions), with the same lazy-load shape as a Claude Code skill:

- A lightweight `<available_skills>` manifest (id/name/description only)
  gets added to system context for whatever model the skill is attached
  to — cheap, always there.
- The model decides, from the `description` alone, whether a request is
  relevant. If so, it calls the builtin `view_skill(id)` tool to load the
  skill's full `content` on demand — verified by reading
  `backend/open_webui/utils/middleware.py` (the `available_skills`/
  `view_skill_ids` block) and `backend/open_webui/tools/builtin.py`'s
  `view_skill()`.
- Skills attach to a model the same way tools/knowledge do —
  `meta.skillIds` on the model's own config (`seed.py` does this via
  `POST /api/v1/models/model/update`) — not a separate resource you pick
  in the chat UI.

This is why `system_prompt.md` (the skill's `content`) doesn't need to be
`gpt-5.6-luna`'s `params.system` override anymore — that field is left
alone, so `gpt-5.6-luna` still behaves like `gpt-5.6-luna` for everything
unrelated, and only pulls in the full ~5,000-token skill instructions when
a request actually matches `SKILL_DESCRIPTION` in `seed.py`. Verified
live: a message containing "quiero escribir un melodrama" gets Etapa 0's
exact first question back (confirming the full skill content loaded,
following the real script rather than improvising from the one-line
description); an unrelated question ("cual es la capital de francia?")
gets answered directly with no melodrama tangent.

## Optional companion: interactive question UI

`system_prompt.md`'s "una pregunta a la vez" flow works as plain text by
default. For a real clickable UI (single-select, multi-select, drag-to-rank)
instead, install the community tool **"Claude-like Ask User Question"** by
Marios Adamidis:
<https://openwebui.com/posts/claude_like_ask_user_question_6d0a6a9b>
(Admin Settings → Tools → Import from Link). Not vendored in this repo —
it's third-party code, install it yourself after reviewing it. Reviewed by
hand before installing on the local dev instance during this build: pure
Python, no network/subprocess/eval calls, renders via OpenWebUI's standard
`execute` event channel. Once installed, it exposes `ask_user_question()`
as a tool the assistant can call for any of this prompt's one-at-a-time
questions.

## Two things this port does natively that the other two platforms can't

**Real parallel alternatives, not a simulation.** OpenWebUI ships a
builtin `delegate_task` tool (real sub-agents, using the current model and
its tools). Its middleware specifically fast-paths multiple `delegate_task`
calls made in the same turn through `asyncio.gather` — every *other* tool
call in a turn runs one at a time, awaited sequentially, but `delegate_task`
calls run concurrently. So when the system prompt says "call
`delegate_task` 3 times in one turn," that's genuine parallel dispatch,
verified by reading `backend/open_webui/utils/middleware.py` directly (see
the `delegate_calls` / `asyncio.gather` block) — not an assumption.

**Live-rendered HTML review reports.** OpenWebUI auto-detects any ` ```html `
fenced code block in a response and renders it live in a side panel
(`Settings → Interface → detect artifacts`, verified in
`src/lib/components/chat/Messages/ContentRenderer.svelte`). So the review
report template is embedded directly in `system_prompt.md` (not put in the
Knowledge collection — see below) and the assistant fills it in and emits
it as a real ` ```html ` block, which renders live with working "Copiar
sugerencia" buttons. No download step, no separate Tool needed.

## Why `review-report-template.html` isn't in the Knowledge collection

Tried it first — Knowledge collections run every file through OpenWebUI's
RAG/embedding pipeline, and this template is mostly CSS/JS with almost no
plain text once tags are stripped. Uploading it 400s with `"The content
provided is empty"` (confirmed against a live instance, not just inferred).
It isn't useful for semantic retrieval anyway. Since the assistant needs to
reproduce it byte-for-byte on demand rather than search it, it's embedded
directly in `system_prompt.md` instead — always available, no retrieval
uncertainty.

## What's verified vs. not (as of this build)

Verified against a live local instance (`docker-compose up`, `docker exec`
into the running container):
- `seed.py` runs end-to-end and is idempotent on re-run.
- `script_guion.py`'s `read_guion`/`write_guion`/`chapter_exists` all
  work correctly against real files, including that the `show_slug`
  sanitizer neutralizes a `../../etc/evil`-style path-traversal attempt
  (it gets collapsed to a harmless slug, not rejected with an error — same
  effect, different mechanism).
- `script_export_docx.py` generates a real, correctly-structured
  `.docx` from realistic (blank-line-separated) script content —
  chapter headings, bolded scene headings, dialogue all come through
  correctly. `python-docx` installs automatically via the tool's
  frontmatter `requirements:` line — no repo dependency changes needed.
- `ENABLE_SUBAGENTS` / `delegate_task` availability, and the
  `asyncio.gather` fast-path for parallel `delegate_task` calls — verified
  by reading the actual OpenWebUI source in this fork, and confirmed
  `ENABLE_SUBAGENTS: true` on the live test instance's config.
- The Artifacts auto-render-on-` ```html ` behavior — verified by reading
  the actual frontend source.

Also verified, once a real tool-calling model (`gpt-5.6-luna`, not the
tiny `qwen2.5:0.5b` from earlier in this build) was available:
- The Skill loads contextually as designed — see "Native Skills" above.
- `reasoning_effort` + function tools work together, which needed
  switching the `gpt-5.6-luna`/`gpt-5.6-terra` connection to the
  Responses API (`api_type: "responses"`) instead of Chat Completions —
  the latter rejects any non-`"none"` `reasoning_effort` when tools are
  attached, for this model family. This is a connection-level setting
  (affects every model on that connection, not just this skill), applied
  after confirming with the connection's owner since it's a shared
  OpenAI API connection, not something scoped to this assistant.

**Not yet verified**: an actual end-to-end chat where the model calls
`delegate_task` 3 times in one turn and the review Artifact renders — the
skill-loading and reasoning+tools mechanics are both confirmed working
individually, but a full run through Etapa 1's real 3-way fan-out plus a
chapter 1/10 review hasn't been exercised end-to-end yet.

## Considered, not integrated: SuperDoc-based `.docx` editor ("OpsUp")

A community post (<https://openwebui.com/posts/opsup_ai_document_editor_for_open_webui_create_edi_d772a6c9>)
describes a Tool that opens a full rich-text `.docx` editor (SuperDoc,
with Word-style Track Changes) as an Artifact in the chat. Looked at it
because it's relevant to `script_export_docx.py`'s output, but not
installing it for now:

- It's a whole separate GitHub repo (`novergeme/opsup`), not a single
  reviewable tool file like `ask_user_question` — its own setup process,
  its own `AGENTS.md`.
- The author's own words: "alpha," "not perfect," "not
  production-hardened," "a working conceptual template to fork, extend,
  and improve." Multiple different architectural approaches across its
  commit history, per the post.
- Doesn't match a real gap in this skill's actual workflow: `guion.md`
  editing already happens conversationally (ask for a rewrite, the
  assistant edits and re-saves via `write_guion`) — `.docx` export is a
  one-shot final step, not an interactive editing surface. Track-Changes
  editing would be a nice-to-have on the exported file, not something the
  current flow is missing.

Worth revisiting if the project matures and there's a specific want for
richer post-export editing UX — not evaluated further than reading the
post (no code reviewed, nothing installed).
