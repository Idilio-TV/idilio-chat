# Melodrama Script Intelligence — multi-platform

A writing partner for libretistas developing Idilio vertical-format
melodrama shows, from a bare idea through a finished chapter-by-chapter
guion — grounded in Peter Brooks' melodrama theory and Idilio's real
`hook_score`/`cliffhanger_score` definitions (from `idilio-marts`).

Originally built as a Claude Code skill in `idilio-marts`. This directory
packages that same content for three platforms:

| Platform | Directory | Parallel alternatives | Persistence | Review output |
|---|---|---|---|---|
| Claude Code | [`claude-plugin/`](claude-plugin/) | Real (`Agent` tool, 3 calls in one message) | `guion.md` file, wherever Claude Code runs | Static HTML file, copy-to-clipboard |
| OpenWebUI | [`openwebui/`](openwebui/) | Real (native `delegate_task`, `asyncio.gather`-parallel) | `guion.md` file on the server | Live-rendered HTML Artifact |
| ChatGPT | [`chatgpt/`](chatgpt/) | Simulated (model generates 2-3 alternatives itself, sequentially, in one turn) | None — chat re-displays the doc for the writer to copy/save | Formatted text (or a downloadable file, if Code Interpreter is on) |

`claude-plugin/skills/melodrama-script-intelligence/reference/` is the
canonical source for the shared reference content (Brooks theory, 12-step
structure, format guide + hook/cliffhanger rubric). `chatgpt/knowledge/`
and `openwebui/knowledge/` are synced copies — run
[`sync-content.sh`](sync-content.sh) after editing anything under
`claude-plugin/`'s `reference/` to keep them in sync.

## Setup

- **Claude Code**: `claude-plugin/` is a real Claude Code plugin. Add this
  repo as a marketplace (`.claude-plugin/marketplace.json` lives at the
  repo root) and install the `melodrama-script-intelligence` plugin.
- **OpenWebUI**: see [`openwebui/README.md`](openwebui/README.md).
- **ChatGPT**: see [`chatgpt/README.md`](chatgpt/README.md).

## Why three versions instead of one

The skill was originally built inside `idilio-marts` (a dbt analytics
repo) — architecturally mismatched, and worse, its own file-writing
behavior would put screenplay drafts inside an analytics repo's working
tree the moment a real libretista used it. Packaging it as installable
content here decouples it from that repo entirely; the three platform
variants exist because Idilio writers may not all use the same tool, and
each platform's actual capabilities (real sub-agents vs. none, real file
persistence vs. none, live-rendered HTML vs. static) genuinely differ
enough that a single write-once instruction set can't serve all three
without either overselling what a weaker platform can do or underselling
what a stronger one can.
