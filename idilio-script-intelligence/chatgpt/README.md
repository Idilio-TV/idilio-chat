# Idilio Script Intelligence — ChatGPT Custom GPT

Adapted from the Claude Code skill at `../claude-plugin/skills/idilio-script-intelligence/`.
GPT creation itself is a manual step in the ChatGPT UI — there's no API for
it — so this bundle just gives you the exact content to paste in.

## Setup

1. Go to [chatgpt.com/gpts/editor](https://chatgpt.com/gpts/editor) → **Create**.
2. **Name:** `Idilio Script Intelligence` (or your own naming).
3. **Instructions:** paste the full contents of [`instructions.md`](instructions.md).
4. **Knowledge:** upload all 4 files from [`knowledge/`](knowledge/):
   - `brooks-theory.md`
   - `structure-12-pasos.md`
   - `format-guide.md`
   - `review-report-template.html`
5. **Capabilities:** turn on **Code Interpreter & Data Analysis** if you want
   the assistant to be able to hand back a real downloadable
   `review-cap<N>.html` file when reviewing a chapter. Without it, reviews
   are still fully functional — they just come back as formatted text in
   the chat instead of a downloadable file.
6. Leave **Web Browsing** and **DALL·E** off — nothing here needs them.
7. Save, test with a real premise, adjust instructions if anything reads
   oddly for your writers.

## What's different from the Claude Code version

- **No real parallel subagents.** ChatGPT can't dispatch parallel work the
  way Claude Code's `Agent` tool does. The instructions tell the assistant
  to generate its 2-3 alternatives itself, sequentially, in one turn — same
  outcome for the writer (real alternatives to compare), different
  mechanism under the hood.
- **No persistent `guion.md`.** ChatGPT has no per-show file it can read and
  append to across sessions. The working document lives in the chat itself;
  the assistant re-displays the full updated document at each milestone so
  the writer can copy/save it on their end, and asks for it back to resume
  a show in a later session.
- **Review reports** are downloadable HTML only if Code Interpreter is
  enabled (step 5 above); otherwise they're formatted text in the chat.

## Keeping this in sync

If the underlying skill (`../claude-plugin/skills/idilio-script-intelligence/`)
changes — new stages, an updated hook/cliffhanger rubric, etc. — the 3
reference files here (everything except `instructions.md`) are meant to be
byte-identical copies of that skill's `reference/*.md` (and the review
template). `instructions.md` is a deliberate adaptation, not a copy — it
needs a human pass to fold in behavior changes, not a blind file copy.
