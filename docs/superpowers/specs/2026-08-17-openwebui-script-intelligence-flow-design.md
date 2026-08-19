# Idilio Script Intelligence (OpenWebUI) — flow redesign

Date: 2026-08-17
Scope: `idilio-script-intelligence/openwebui/SKILL.md` only. The Claude Code
plugin (`claude-plugin/`) and ChatGPT (`chatgpt/`) variants are explicitly
out of scope — this need is OpenWebUI-specific.

## Problem

Two complaints from libretistas using the OpenWebUI variant:

1. Character work (Etapa 1: protagonist) happens before the plot argument
   (Etapa 2), so the writer is picking a protagonist before the story's
   central conflict exists to shape that choice.
2. Decision fatigue: many sequential one-at-a-time questions across 7
   stages (Etapa 0–6), with no visibility into how many are left or where
   the writer currently stands. It also currently jumps character → plot →
   reparto → structure → chapters without ever showing the writer "here's
   your argument and cast, fully formed" before script writing starts.

## Design

### 1. Stage reorder (7 stages → 6)

| New # | Stage | Change |
|---|---|---|
| Etapa 0 | Setup | unchanged |
| Etapa 1 | Argumento y hook | moved up (was Etapa 2) |
| Etapa 2 | Personajes | merged (was Etapa 1 protagonist + Etapa 3 reparto) |
| Etapa 3 | Estructura de 12 pasos | renumbered (was Etapa 4) |
| Etapa 4 | Giros y climax | renumbered (was Etapa 5) |
| Etapa 5 | Escritura por capítulo | renumbered (was Etapa 6) |

`guion.md`'s document sections are unaffected — only the conversational
order the skill fills them in changes.

### 2. Etapa 1 — Argumento y hook (now first)

Same 3 pre-questions as the old Etapa 2 (central melodramatic/amorous
conflict, villain and what they need to win, information asymmetry between
audience and protagonist) — asked as ONE grouped multi-part message (see
§5) since there's no chosen character yet to anchor separate questions to.

`delegate_task` x3 (unchanged mechanism), each proposal's PLOT ARGUMENTAL
paragraph now includes a one-line **unnamed protagonist sketch** (e.g. "a
young nurse hiding her sister's debt") folded into the prose, since no
character has been chosen yet at this point. Writer picks/combines one;
written to `## Plot Argumental`.

### 3. Etapa 2 — Personajes (the "Ngram" character grid)

Pre-questions: merge old Etapa 1 (protagonist) + Etapa 3 (reparto)
questions into 2 grouped multi-part messages (see §5):

- Group A (protagonist-shaping): quién sufre más, de quién se enamora o
  con quién sufre el público, víctima o protector.
- Group B (reparto-shaping): quién protege al protagonista, qué gesto
  delata al villano ("cuerpo como prueba"), si hay un falso aliado.

Then `delegate_task` x3 in parallel (same fan-out mechanism as today),
each returning one **complete cast grid** as a markdown table:

| Rol | Nombre | Propósito | Obstáculo | Oculto moral / rasgo delator | Polarización |
|---|---|---|---|---|---|
| Protagonista | ... | ... | ... | ... | buena |
| Villano | ... | ... | ... | ... | mala |
| Aliado | ... | ... | ... | ... | buena |
| Falso aliado (si aplica) | ... | ... | ... | ... | ... |

Each grid is grounded in the plot argumental chosen in Etapa 1. Writer can
pick one grid wholesale, or mix rows across grids ("protagonist from grid
2, villain from grid 1"). Final combined cast written to `## Personajes`.

This replaces the old Etapa 1 (protagonist-only, 3 prose alternatives) and
Etapa 3 (reparto, no alternatives by default) entirely.

### 4. Progress line (every non-review response)

A one-line tracker prepended before the actual content of **every**
response in the conversation (from the first Setup question onward), using
unicode glyphs, not emoji. **Exception:** Review responses (the HTML
report) are always and only the ` ```html ` block — no progress line
precedes them (see "Review" section in SKILL.md).

```
Paso 3/6 · Personajes — ✓ Setup ✓ Argumento ▶ Personajes ○ Estructura ○ Giros ○ Escritura
```

- `✓` done, `▶` current, `○` pending — all 6 stages always listed.
- Replaces the existing "✅ Etapa X lista — ..." transition-summary
  sentence (dropped to avoid saying the same thing twice per turn).

### 5. Reducing question volume (grouped multi-part questions)

Amend the global rule "Una pregunta a la vez, nunca varias en el mismo
turno" to distinguish:

- **Grouping related sub-questions of one topic into one multi-part
  message** — now allowed, still presented in the existing numbered-list +
  "Otro" format (one numbered list per sub-question, stacked in the same
  message), writer replies once covering all parts.
- **Stacking unrelated questions** — still forbidden.

Applied to:

- Etapa 1 Argumento: 3 questions → 1 grouped message.
- Etapa 2 Personajes: up to 6 questions → 2 grouped messages (Group A,
  Group B per §3).
- Etapa 4 Giros: 2 questions → 1 grouped message.

Left unchanged: Etapa 0 Setup (4 structurally distinct questions, each
gates document creation), Etapa 3 12-pasos (inherently step-by-step by
technique), Etapa 5 per-chapter (already asks objetivo dramático + gancho
de cierre together).

## Out of scope

- `claude-plugin/` and `chatgpt/` variants — not touched.
- `reference/`/`knowledge/` content files (brooks-theory, format-guide,
  structure-12-pasos, review-report-template) — unaffected, no sync needed.
- Review flow (panel completo / batch / HTML report) — unaffected.
