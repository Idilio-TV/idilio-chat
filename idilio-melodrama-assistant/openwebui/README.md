# Melodrama Script Intelligence — OpenWebUI

The most faithful port of the three platforms in this directory — unlike
the Claude Code plugin (via the `Agent` tool) and the ChatGPT bundle (no
real tools at all), OpenWebUI gives this assistant **real parallel
sub-agents and real file persistence**, running on this server.

## Setup

1. Bring up `idilio-chat` (`docker-compose up -d` from the repo root) and
   make sure a model is available (e.g. `docker exec ollama ollama pull
   <model>`, or configure an OpenAI-compatible connection in Admin
   Settings).
2. Run the seed script:
   ```bash
   cd idilio-melodrama-assistant/openwebui
   python3 seed.py --base-url http://localhost:3000 \
       --email you@idilio.tv --password '...'
   ```
   This registers the 2 custom tools (`melodrama_guion`,
   `melodrama_export_docx`), creates the "Melodrama Script Intelligence"
   Knowledge collection, uploads the 3 reference `.md` files into it, and
   checks that subagents are enabled. Safe to re-run — it updates existing
   tools and skips files/knowledge that already match.
3. In the OpenWebUI admin UI: **Workspace → Models → new model preset.**
   - System Prompt: paste [`system_prompt.md`](system_prompt.md) in full.
   - Attach the 2 `melodrama_*` tools.
   - Attach the "Melodrama Script Intelligence" knowledge collection.
4. If `seed.py` warned that subagents are off: **Admin Settings →
   Subagents → Enable Subagents.** (On a fresh instance this defaults to
   off; enable once, server-wide.)

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
- `melodrama_guion.py`'s `read_guion`/`write_guion`/`chapter_exists` all
  work correctly against real files, including that the `show_slug`
  sanitizer neutralizes a `../../etc/evil`-style path-traversal attempt
  (it gets collapsed to a harmless slug, not rejected with an error — same
  effect, different mechanism).
- `melodrama_export_docx.py` generates a real, correctly-structured
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

**Not yet verified**: an actual end-to-end chat where a tool-calling model
calls `delegate_task` 3 times and the review Artifact renders correctly.
The only model available during this build was a tiny test model
(`qwen2.5:0.5b`) unlikely to reliably use tool-calling — this needs a real
run with whatever model you actually deploy.
