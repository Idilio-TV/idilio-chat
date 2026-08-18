# OpenWebUI Script Intelligence Flow Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorder the OpenWebUI script-intelligence skill so plot argument
comes before character work, merge protagonist + reparto into one
grid-based character stage, add a per-response unicode progress line, and
group related pre-questions to cut question volume — addressing writer
decision fatigue and premature script-writing.

**Architecture:** This is a single prompt file (`openwebui/SKILL.md`, plain
markdown instructions consumed by an LLM at runtime, not executable code).
There is no test suite or build step. Each task edits one contiguous
section of the file; "testing" means grepping for stale references and
re-reading the edited section to confirm it reads correctly and is
internally consistent with the rest of the file.

**Tech Stack:** Markdown only. No code, no dependencies.

## Global Constraints

- Scope is `idilio-script-intelligence/openwebui/SKILL.md` only. Do not
  touch `claude-plugin/` or `chatgpt/` — this need is OpenWebUI-specific
  (per spec).
- Do not touch `openwebui/knowledge/*.md` (reference content) — unaffected.
- Progress-line glyphs are unicode, never emoji: `✓` done, `▶` current,
  `○` pending (exact spec, §4).
- Stage order (6 stages total): Setup, Argumento, Personajes, Estructura,
  Giros, Escritura (spec §1).
- `guion.md`'s document sections (`## Plot Argumental`, `## Personajes`,
  etc.) are unaffected — only conversational order changes (spec §1).
- Full design spec: `docs/superpowers/specs/2026-08-17-openwebui-script-intelligence-flow-design.md`.

---

## Task 1: Update the `delegate_task` example for the new Etapa 1

**Files:**
- Modify: `idilio-script-intelligence/openwebui/SKILL.md:48-58`

**Interfaces:**
- Consumes: nothing from other tasks (self-contained text edit).
- Produces: nothing consumed by later tasks — this is a standalone
  illustrative example block.

The current example under "Alternativas en paralelo" shows a
`delegate_task` call for the old Etapa 1 (protagonist-only). Since Etapa 1
is now Argumento (plot comes before any named character), this example
must show a plot-argumental + hook call instead, with an unnamed
protagonist sketch folded into the prose (spec §2).

- [ ] **Step 1: Replace the example block**

Read `idilio-script-intelligence/openwebui/SKILL.md` lines 44-58 to confirm
current content, then use Edit with:

old_string:
```
Ejemplo para la Etapa 1:

> task: "Eres guionista de melodrama para shows verticales cortos. Propón
> UN protagonista para este universo. Devuelve: 1) nombre y una línea de
> descripción, 2) propósito central, 3) obstáculo/antagonista central, 4)
> por qué este personaje es la mejor puerta de entrada al 'oculto moral' de
> la historia. No escribas escenas todavía."
> context: "Universo: {universo}. Contexto del libretista: {respuestas}."

Presenta las alternativas devueltas lado a lado; el libretista elige o
combina.
```

new_string:
```
Ejemplo para la Etapa 1 (Argumento):

> task: "Eres guionista de melodrama para shows verticales cortos, estilo
> Idilio. Escribe: 1) PLOT ARGUMENTAL: un párrafo de 60-120 palabras
> presentando un boceto de protagonista SIN NOMBRE (una línea describiéndolo
> por su rol/situación, ej. 'una joven enfermera que oculta la deuda de su
> hermana' — todavía no se ha elegido un personaje, eso pasa en la Etapa 2),
> su propósito amoroso central, y el obstáculo/villano. Cierra
> opcionalmente con una pregunta retórica tipo gancho. 2) HOOK DE ARRANQUE:
> 1-2 líneas describiendo la primera imagen o línea de diálogo del capítulo
> 1, diseñada para que nadie abandone en los primeros segundos."
> context: "Universo: {universo}. Contexto del libretista: {respuestas}."

Presenta las 3 alternativas devueltas lado a lado; el libretista elige o
combina.
```

- [ ] **Step 2: Verify**

Run: `grep -n "Ejemplo para la Etapa" idilio-script-intelligence/openwebui/SKILL.md`
Expected: one match, now reading "Ejemplo para la Etapa 1 (Argumento):".

Run: `grep -n "Propón\s*$\|UN protagonista para este universo" idilio-script-intelligence/openwebui/SKILL.md`
Expected: no matches (old protagonist-only example text is gone).

- [ ] **Step 3: Commit**

```bash
cd idilio-script-intelligence
git add openwebui/SKILL.md
git commit -m "openwebui skill: update Etapa 1 example to argumento+hook"
```

---

## Task 2: Add the Progreso section and update "Cómo hacer preguntas" for grouped questions

**Files:**
- Modify: `idilio-script-intelligence/openwebui/SKILL.md:73-104` (Cómo
  hacer preguntas section) and insert a new `# Progreso` section
  immediately after it (before `# Reglas generales de conversación`,
  currently starting at line 106).

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: the `# Progreso` section that Task 3 (Reglas generales) and
  Task 4 (Etapas) will reference by name ("ver 'Progreso' arriba").

- [ ] **Step 1: Add the grouped-question rule and example to "Cómo hacer preguntas"**

Read `idilio-script-intelligence/openwebui/SKILL.md` lines 73-105 to
confirm current content, then use Edit with:

old_string:
```
- Cuando el libretista responda con un número, tradúcelo tú mismo a la
  opción correspondiente antes de seguir — no le pidas que repita el texto.
- Nunca combines dos preguntas en una sola lista — sigue siendo una
  pregunta a la vez, solo que ahora con opciones numeradas.
```

new_string:
```
- Cuando el libretista responda con un número, tradúcelo tú mismo a la
  opción correspondiente antes de seguir — no le pidas que repita el texto.
- **Nunca combines dos preguntas distintas en una sola lista numerada** —
  cada sub-pregunta tiene su propia lista de opciones. Sí puedes **agrupar
  varias sub-preguntas relacionadas del mismo tema** en un solo mensaje
  cuando la etapa lo indica (ver Etapa 1, Etapa 2 y Etapa 4 en "Etapas" más
  abajo): repite el patrón completo (pregunta + lista numerada + "Otro")
  una vez por sub-pregunta, numerando las sub-preguntas mismas como 1),
  2), 3)... El libretista responde a todas en el mismo mensaje. Esto no
  rompe "una pregunta a la vez" — es una sola etapa preguntada de una vez,
  nunca mezcles preguntas de dos etapas distintas en el mismo turno.

Ejemplo de mensaje agrupado (Etapa 1 — Argumento):

```
1) ¿Cuál es el conflicto melodramático central? Piensa en un propósito
   amoroso: ¿qué amor se busca, se protege, o se pierde?

   1. Un amor prohibido que hay que proteger
   2. Una herencia o legado que hay que recuperar
   3. Un secreto familiar que hay que ocultar o revelar
   Otro: escríbelo tú

2) ¿Quién es el villano y qué necesita conseguir para ganar?

   1. Un rival que quiere el mismo amor
   2. Un familiar que quiere el control del legado
   3. Alguien que quiere exponer o silenciar el secreto
   Otro: escríbelo tú

3) ¿Qué necesita ver o saber el público que el protagonista todavía no
   sabe (o al revés)?

   1. El público sabe algo que el protagonista no sabe todavía
   2. El protagonista sabe algo que el público no sabe todavía
   3. Ninguno de los dos lo sabe todavía — se revela después, a ambos a la vez
   Otro: escríbelo tú
```
```

- [ ] **Step 2: Insert the new `# Progreso` section**

Use Edit with:

old_string:
```
# Reglas generales de conversación

- Una pregunta a la vez. Nunca varias preguntas en el mismo turno — espera
  la respuesta antes de seguir.
```

new_string:
```
# Progreso — línea de estado en cada respuesta

Toda respuesta de esta skill —desde la primera pregunta de la sesión en
adelante— empieza con una línea de estado de una sola línea, con este
formato exacto, **excepto** cuando la respuesta es un reporte de review
(ver "Review" más abajo): esas respuestas siguen siendo siempre y
únicamente el bloque ```html, sin la línea de estado ni ningún otro texto
antes.

```
Paso {N}/6 · {etapa actual} — {las 6 etapas con su símbolo}
```

Símbolos (unicode, nunca emoji): `✓` etapa ya cerrada, `▶` etapa actual,
`○` etapa pendiente. Las 6 etapas, en este orden fijo: Setup, Argumento,
Personajes, Estructura, Giros, Escritura.

Ejemplo, a mitad de la Etapa 2:

```
Paso 3/6 · Personajes — ✓ Setup ✓ Argumento ▶ Personajes ○ Estructura ○ Giros ○ Escritura
```

Esta línea reemplaza el resumen de cierre de etapa ("✅ Etapa X lista —
...") que se usaba antes — ya no hace falta esa frase aparte, la línea de
estado cumple esa función en cada turno.

# Reglas generales de conversación

- Una pregunta a la vez, salvo que la etapa agrupe varias sub-preguntas
  relacionadas en un solo mensaje multi-parte (ver "Cómo hacer preguntas"
  y las etapas de Argumento, Personajes y Giros en "Etapas" más abajo) —
  eso sigue siendo una sola etapa preguntada de una vez, nunca mezcles
  preguntas de dos etapas distintas en el mismo turno. Espera la respuesta
  completa antes de seguir.
```

- [ ] **Step 3: Verify**

Run: `grep -n "^# Progreso" idilio-script-intelligence/openwebui/SKILL.md`
Expected: one match.

Run: `grep -n "Paso {N}/6\|✓.*▶.*○" idilio-script-intelligence/openwebui/SKILL.md`
Expected: format line and example line both present.

Run: `grep -n "Nunca varias preguntas en el mismo turno" idilio-script-intelligence/openwebui/SKILL.md`
Expected: no matches (old unqualified wording replaced).

- [ ] **Step 4: Commit**

```bash
cd idilio-script-intelligence
git add openwebui/SKILL.md
git commit -m "openwebui skill: add progress line and grouped-question rule"
```

---

## Task 3: Update the rest of "Reglas generales de conversación" to reference the progress line

**Files:**
- Modify: `idilio-script-intelligence/openwebui/SKILL.md` (the bullet list
  right after the header edited in Task 2 — originally lines 108-119,
  shifted down by Task 2's insertion; locate by content, not line number).

**Interfaces:**
- Consumes: the `# Progreso` section name from Task 2.
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Replace the orientation bullet**

Read the file to find the current "Mantén al libretista orientado..."
bullet (it now follows the bullet edited in Task 2, Step 2), then use Edit
with:

old_string:
```
- Conecta brevemente cada pregunta con el porqué (la teoría detrás).
- Mantén al libretista orientado en conversaciones largas: antes de cada
  pregunta que no sea la primera de toda la sesión, resume en 1-2 líneas
  qué ya quedó definido hasta ahora y qué falta en la etapa actual. Al
  cerrar una etapa completa, antes de pasar a la siguiente, resume en una
  línea qué etapas ya están listas y cuáles faltan.
```

new_string:
```
- Conecta brevemente cada pregunta con el porqué (la teoría detrás).
- Toda respuesta empieza con la línea de estado (ver "Progreso" arriba) —
  eso ya mantiene al libretista orientado sobre qué etapa está activa y
  cuántas faltan. Además, antes de cada pregunta que no sea la primera de
  toda la sesión, resume en 1-2 líneas qué ya quedó definido hasta ahora y
  qué falta en la etapa actual.
```

- [ ] **Step 2: Verify**

Run: `grep -n "Al cerrar una etapa completa" idilio-script-intelligence/openwebui/SKILL.md`
Expected: no matches (superseded by the progress line).

Run: `grep -n 'ver "Progreso" arriba' idilio-script-intelligence/openwebui/SKILL.md`
Expected: at least one match.

- [ ] **Step 3: Commit**

```bash
cd idilio-script-intelligence
git add openwebui/SKILL.md
git commit -m "openwebui skill: point orientation rule at the progress line"
```

---

## Task 4: Rewrite the `# Etapas` section — reorder, merge, and add grouped questions

**Files:**
- Modify: `idilio-script-intelligence/openwebui/SKILL.md` (the `# Etapas`
  section, originally lines 154-230, shifted down by Tasks 2-3's
  insertions; locate by content).

**Interfaces:**
- Consumes: the `# Progreso` and grouped-question conventions from Tasks
  2-3.
- Produces: final stage numbering (Etapa 0-5) and names that the Review
  section already refers to only by chapter number, not stage name/number
  — confirmed by grep in Task 5, so no further downstream consumers.

This is the core content change: argument before characters (spec §2),
protagonist + reparto merged into one grid-based stage (spec §3), and
grouped questions in Argumento/Personajes/Giros (spec §5).

- [ ] **Step 1: Replace the entire `# Etapas` section**

Read the file to find the current `# Etapas` section (starts at the line
containing exactly `# Etapas` and ends right before `# Review`), then use
Edit with:

old_string:
```
# Etapas

**Etapa 0 — Setup.** Una pregunta numerada a la vez (ver "Cómo hacer
preguntas"):

1. "Cuéntame la idea general de tu historia — puede ser un párrafo suelto,
   una premisa a medio armar, o el tema que quieres explorar." opciones: 1)
   Ya tengo una idea (aunque sea suelta) — la escribo, 2) Empecemos
   totalmente desde cero. Otro: escríbelo tú.
2. "¿Cuál es el universo o género de esta historia?" opciones: 1) Venganza
   / herencia familiar, 2) Romance imposible, 3) Mafia y redención, 4)
   Sobrenatural, 5) Drama médico / secretos de familia. Otro: escríbelo tú.
   (Si la idea de la pregunta 1 ya sugiere un género, dilo explícitamente y
   ofrece esa opción primero — "por lo que cuentas, esto suena a X, ¿es así
   o lo ves distinto?" — en vez de preguntar desde cero.)
3. "¿Ya tienes un título provisional, o lo definimos juntos?" opciones: 1)
   Ya tengo un título — lo escribo, 2) Definámoslo juntos sobre la marcha
   (si elige esta, sugiere 2-3 títulos basados en la idea y el universo ya
   definidos, no la dejes en blanco). Otro: escríbelo tú.

   En cuanto tengas un título (de esta pregunta, o de lo que se acuerde
   juntos), llama `read_guion` con el slug que le corresponda — si ya
   existe, pregunta si se retoma en vez de seguir con el resto de Etapa 0
   (nunca lo sobreescribas sin confirmación).

4. "¿Cuántos capítulos tienes en mente?" opciones: 1) 45-72 capítulos
   (típico en Idilio) — el capítulo 11 es donde empieza el muro de pago,
   así que el capítulo 10 necesita un cliffhanger especialmente fuerte, 2)
   Menos de 10 (prueba o show corto) — "capítulo 10" pasa a ser el último
   capítulo del show en el resto de esta skill. Otro: escribe el número.

Llama `write_guion` con el documento inicial. Resume en una línea: "✅
Etapa 0 lista — idea, universo, título y capítulos definidos. Siguiente:
Etapa 1 — Personaje y premisa."

**Etapa 1 — Personaje y premisa.** Pregunta quién sufre más en este
universo, de quién quiere que el público se enamore, si el protagonista es
más víctima o protector. Usa `delegate_task` x3 (ver arriba) pidiendo una
propuesta de protagonista cada uno (nombre, propósito, obstáculo, por qué
es la mejor puerta al "oculto moral"). El libretista elige o combina;
guarda el resultado con `write_guion`.

**Etapa 2 — Argumento y hook.** Pregunta el conflicto melodramático
central, quién es el villano, qué sabe el público que el protagonista no
sabe. `delegate_task` x3 pidiendo plot argumental (60-120 palabras) + hook
de arranque cada uno. Guarda la elección.

**Etapa 3 — Reparto y polarización moral.** Pregunta quién protege al
protagonista, qué gesto delata al villano, si hay un falso aliado. No hace
falta `delegate_task` por defecto. Si el libretista pide explícitamente
alternativas de villano o aliado, ofrece 2-3 propuestas (un `delegate_task`
por propuesta, o generadas directamente por ti si son variaciones
menores). Guarda el reparto completo, marcando quién es bueno/malo y su
gesto delator.

**Etapa 4 — Estructura de 12 pasos.** Usa `structure-12-pasos.md`.
Pregunta paso a paso qué ocurre en cada uno de los 12 pasos. Define la
cuestión central; deja giros/clímax pendientes para la Etapa 5.

**Etapa 5 — Giros y climax.** Pregunta qué información oculta cambia todo
al revelarse, cómo se resuelve todo. `delegate_task` x2 o x3 pidiendo cada
uno un paquete de 2-3 giros + clímax + desenlace (giros ganados, no
forzados; clímax con un "tableau").

**Etapa 6 — Escritura por capítulo.** Antes de anexar, llama
`chapter_exists`. Si ya existe, pregunta si se reemplaza (y renumera
escenas siguientes si cambia la cantidad) o si el número está mal. Si no
existe: pregunta el objetivo dramático y el gancho de cierre; si se piden
alternativas de escena, usa `delegate_task`. Anexa con `write_guion`
(documento completo, no solo el capítulo nuevo). Todo capítulo termina en
gancho/cliffhanger. Recuerda: el número de capítulo es 1:1 con el
`episode_number` real de producción (ver `format-guide.md`) — capítulo 1
es donde se juega el hook, capítulo 10 el último antes del muro de pago y
donde se juega el cliffhanger más importante. **Al terminar de escribir el
capítulo 1 o el capítulo 10 (o el último, en shows cortos), dispara
automáticamente el panel completo de review (ver "Review" más abajo) antes
de seguir con el siguiente capítulo** — no te limites a avisar, hazlo.
```

new_string:
```
# Etapas

**Etapa 0 — Setup.** Una pregunta numerada a la vez (ver "Cómo hacer
preguntas"):

1. "Cuéntame la idea general de tu historia — puede ser un párrafo suelto,
   una premisa a medio armar, o el tema que quieres explorar." opciones: 1)
   Ya tengo una idea (aunque sea suelta) — la escribo, 2) Empecemos
   totalmente desde cero. Otro: escríbelo tú.
2. "¿Cuál es el universo o género de esta historia?" opciones: 1) Venganza
   / herencia familiar, 2) Romance imposible, 3) Mafia y redención, 4)
   Sobrenatural, 5) Drama médico / secretos de familia. Otro: escríbelo tú.
   (Si la idea de la pregunta 1 ya sugiere un género, dilo explícitamente y
   ofrece esa opción primero — "por lo que cuentas, esto suena a X, ¿es así
   o lo ves distinto?" — en vez de preguntar desde cero.)
3. "¿Ya tienes un título provisional, o lo definimos juntos?" opciones: 1)
   Ya tengo un título — lo escribo, 2) Definámoslo juntos sobre la marcha
   (si elige esta, sugiere 2-3 títulos basados en la idea y el universo ya
   definidos, no la dejes en blanco). Otro: escríbelo tú.

   En cuanto tengas un título (de esta pregunta, o de lo que se acuerde
   juntos), llama `read_guion` con el slug que le corresponda — si ya
   existe, pregunta si se retoma en vez de seguir con el resto de Etapa 0
   (nunca lo sobreescribas sin confirmación).

4. "¿Cuántos capítulos tienes en mente?" opciones: 1) 45-72 capítulos
   (típico en Idilio) — el capítulo 11 es donde empieza el muro de pago,
   así que el capítulo 10 necesita un cliffhanger especialmente fuerte, 2)
   Menos de 10 (prueba o show corto) — "capítulo 10" pasa a ser el último
   capítulo del show en el resto de esta skill. Otro: escribe el número.

Llama `write_guion` con el documento inicial. Siguiente etapa: Etapa 1 —
Argumento y hook.

**Etapa 1 — Argumento y hook.** Todavía no hay ningún personaje elegido —
el argumento se define primero, el reparto se construye después para que
encaje con él (Etapa 2). Agrupa estas 3 sub-preguntas en un solo mensaje
multi-parte (ver "Cómo hacer preguntas"): el conflicto melodramático
central (piensa en un propósito amoroso: qué amor se busca, se protege, o
se pierde), quién es el villano y qué necesita conseguir para ganar, y qué
necesita ver o saber el público que el protagonista todavía no sabe (o al
revés). Con las respuestas, `delegate_task` x3 (ver arriba) pidiendo cada
uno PLOT ARGUMENTAL (60-120 palabras, con un boceto de protagonista SIN
NOMBRE — descrito por su rol/situación, ej. "una joven enfermera que oculta
la deuda de su hermana", ya que el personaje se elige recién en la Etapa
2) + HOOK de arranque (1-2 líneas, la primera imagen o línea del capítulo
1). Presenta las 3 alternativas; el libretista elige o combina. Guarda el
resultado con `write_guion` en `## Plot Argumental`. Siguiente etapa:
Etapa 2 — Personajes.

**Etapa 2 — Personajes.** Con el argumento ya definido, agrupa estas
sub-preguntas en 2 mensajes multi-parte (ver "Cómo hacer preguntas"):

- Grupo A (protagonista): quién sufre más en este universo, de quién
  quieres que el público se enamore o con quién quieres que sufra, si el
  protagonista es más víctima, más protector, o ambos a la vez.
- Grupo B (reparto): quién protege al protagonista, qué gesto o rasgo
  delata al villano ante el público aunque los demás personajes todavía no
  lo vean (esto es el "cuerpo como prueba" de `brooks-theory.md` —
  explícaselo brevemente si el libretista no está familiarizado), si hay
  algún falso aliado (alguien que parece bueno pero no lo es, o al revés).

Con las respuestas de ambos grupos, `delegate_task` x3 en paralelo (mismo
mecanismo de fan-out, ver "Alternativas en paralelo"), cada uno pidiendo el
REPARTO COMPLETO como una tabla markdown, con una fila por personaje
(Protagonista, Villano, Aliado, y Falso aliado si aplica) y estas columnas:
Rol, Nombre, Propósito, Obstáculo, Oculto moral / rasgo delator,
Polarización (buena/mala). Cada propuesta debe encajar con el plot
argumental ya elegido en la Etapa 1. Presenta las 3 tablas lado a lado; el
libretista puede elegir una completa o mezclar filas entre tablas (ej.
"protagonista de la tabla 2, villano de la tabla 1"). Guarda el reparto
final combinado con `write_guion` en `## Personajes`, marcando para cada
personaje si es claramente bueno o malo y cuál es su gesto delator.
Siguiente etapa: Etapa 3 — Estructura de 12 pasos.

**Etapa 3 — Estructura de 12 pasos.** Usa `structure-12-pasos.md`.
Pregunta paso a paso qué ocurre en cada uno de los 12 pasos. Define la
cuestión central; deja giros/clímax pendientes para la Etapa 4.

**Etapa 4 — Giros y climax.** Agrupa estas 2 sub-preguntas en un solo
mensaje multi-parte: qué información oculta cambia todo al revelarse, y
cómo se resuelve todo al final. `delegate_task` x2 o x3 pidiendo cada uno
un paquete de 2-3 giros + clímax + desenlace (giros ganados, no forzados;
clímax con un "tableau").

**Etapa 5 — Escritura por capítulo.** Antes de anexar, llama
`chapter_exists`. Si ya existe, pregunta si se reemplaza (y renumera
escenas siguientes si cambia la cantidad) o si el número está mal. Si no
existe: pregunta el objetivo dramático y el gancho de cierre; si se piden
alternativas de escena, usa `delegate_task`. Anexa con `write_guion`
(documento completo, no solo el capítulo nuevo). Todo capítulo termina en
gancho/cliffhanger. Recuerda: el número de capítulo es 1:1 con el
`episode_number` real de producción (ver `format-guide.md`) — capítulo 1
es donde se juega el hook, capítulo 10 el último antes del muro de pago y
donde se juega el cliffhanger más importante. **Al terminar de escribir el
capítulo 1 o el capítulo 10 (o el último, en shows cortos), dispara
automáticamente el panel completo de review (ver "Review" más abajo) antes
de seguir con el siguiente capítulo** — no te limites a avisar, hazlo.
```

- [ ] **Step 2: Verify stage count and names**

Run: `grep -n "^\*\*Etapa" idilio-script-intelligence/openwebui/SKILL.md`
Expected: exactly 6 matches, in this order: `Etapa 0 — Setup.`,
`Etapa 1 — Argumento y hook.`, `Etapa 2 — Personajes.`,
`Etapa 3 — Estructura de 12 pasos.`, `Etapa 4 — Giros y climax.`,
`Etapa 5 — Escritura por capítulo.`

Run: `grep -n "Personaje y premisa\|Etapa 6\|Etapa.*Reparto" idilio-script-intelligence/openwebui/SKILL.md`
Expected: no matches (old stage names/numbers fully gone).

- [ ] **Step 3: Commit**

```bash
cd idilio-script-intelligence
git add openwebui/SKILL.md
git commit -m "openwebui skill: reorder stages, merge character grid, group questions"
```

---

## Task 5: Full-file consistency pass

**Files:**
- Read only: `idilio-script-intelligence/openwebui/SKILL.md` (whole file)

**Interfaces:**
- Consumes: the complete edited file from Tasks 1-4.
- Produces: nothing — this is the final verification gate before the
  branch is considered done.

- [ ] **Step 1: Read the whole file top to bottom**

Read `idilio-script-intelligence/openwebui/SKILL.md` in full and confirm:
- The `# Progreso` section appears once, between "Cómo hacer preguntas"
  and "Reglas generales de conversación".
- "Reglas generales de conversación" references "Progreso" and no longer
  contains the old "Al cerrar una etapa completa..." sentence.
- The "# Etapas" section lists exactly 6 stages (0-5) in the new order,
  with Etapa 1 = Argumento, Etapa 2 = Personajes (grid table columns
  present), Etapa 3 = Estructura, Etapa 4 = Giros, Etapa 5 = Escritura.
- The "Alternativas en paralelo" example (line ~48-58 originally) matches
  Etapa 1's new content (argumento + hook, not protagonist).
- The `# Review` section is untouched — it references "capítulo 1" /
  "capítulo 10" only, never an Etapa number, so it needed no changes.

- [ ] **Step 2: Grep sweep for stale references**

Run: `grep -n "Etapa 6\|Etapa 1 — Personaje\|Etapa 2 — Argumento\|Etapa 3 — Reparto\|Etapa 4 — Estructura\|Etapa 5 — Giros" idilio-script-intelligence/openwebui/SKILL.md`
Expected: no matches — confirms no old-numbering references survived
anywhere in the file (including inside the Review section or elsewhere
outside the `# Etapas` block).

- [ ] **Step 3: Confirm no other files were touched**

Run: `git diff --name-only $(git merge-base HEAD main) HEAD`
Expected: only `openwebui/SKILL.md` (plus any docs committed alongside it)
shows as changed across the branch — `claude-plugin/`, `chatgpt/`, and
`openwebui/knowledge/` untouched. Then run `git status --short` to confirm
the working tree is clean (no uncommitted changes).

- [ ] **Step 4: Report**

No commit needed for this task (read-only verification). If Step 2 or 3
finds anything, fix it in the relevant earlier task's section and re-run
this task's checks before considering the plan complete.
