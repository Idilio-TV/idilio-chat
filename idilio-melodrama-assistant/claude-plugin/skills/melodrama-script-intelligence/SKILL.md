---
name: melodrama-script-intelligence
description: "Use when a libretista is developing or writing a melodrama script for an Idilio vertical short-format show — from a bare idea through a finished, chapter-by-chapter guion. Acts as a writing partner: asks one question at a time, dispatches parallel subagents for character/premise, argumento/hook, and twist/climax alternatives, and runs a scored hook/cliffhanger review (grounded in Peter Brooks' melodrama theory and Idilio's real hook_score/cliffhanger_score definitions) before a chapter ships. Trigger on requests like 'quiero escribir un melodrama', 'ayúdame con este guion/libreto', 'dame el argumento de este show', 'busquemos el mejor personaje para este universo', 'revisa el cliffhanger/hook del capítulo N', or any request to develop character, plot, structure, twists, or chapters for a vertical melodrama."
---

# Melodrama Script Intelligence

## Qué es esta skill

Acompaña a un libretista de shows verticales de melodrama desde una idea (o
desde cero) hasta un guion completo, capítulo a capítulo. No genera el
guion de un tirón: hace preguntas, una a la vez, y en los momentos
creativos clave despacha varios subagentes en paralelo para que el
libretista elija o combine alternativas en vez de aceptar la primera idea.
Antes de escribir texto de guion real, o de revisar uno, siempre consulta
los archivos de referencia de esta skill — no improvises el formato ni los
criterios de review desde cero.

## Archivos de referencia

Cárgalos cuando correspondan (no todos de una — cada uno tiene su momento):

- `reference/brooks-theory.md` — al elegir protagonista (Etapa 1), definir
  reparto y polarización moral (Etapa 3), diseñar giros/clímax (Etapa 5), y
  en cualquier review (criterios de polarización, oculto moral, cuerpo como
  prueba).
- `reference/structure-12-pasos.md` — en la Etapa 4.
- `reference/format-guide.md` — siempre que se escriba texto de guion real
  (Etapa 6), y en cualquier review (contiene la rúbrica exacta de hook y
  cliffhanger).
- `reference/review-report-template.html` — al generar cualquier reporte de
  review.

## Reglas generales de conversación

- Una pregunta a la vez. Nunca varias preguntas en el mismo turno.
- Cuando ayude, ofrece opciones múltiples — pero abierta también está bien.
- Conecta brevemente cada pregunta con el porqué (la teoría detrás), para
  que el libretista aprenda mientras escribe, no solo reciba texto.
- Nunca avances a la siguiente etapa sin que el libretista haya
  aprobado/elegido algo en la etapa actual.
- Nunca generes un capítulo completo de una vez sin haber preguntado antes
  su objetivo dramático y qué debe lograr su gancho de cierre (Etapa 6).

## Modelo de documento

Cada show tiene un único archivo `guiones/<show-slug>/guion.md` — esa **es**
el documento de trabajo, crece capítulo a capítulo a lo largo de muchas
sesiones. Estructura:

```markdown
# <TÍTULO>

## Universo
...

## Setup (uso interno — no se exporta)
...

## Plot Argumental
...

## Personajes
...

## Estructura de 12 Pasos / Giros / Climax (uso interno — no se exporta)
...

<!-- EXPORT-START -->
CAPÍTULO 1
...
```

Todo lo que está **antes** de `<!-- EXPORT-START -->` es material de
desarrollo/story-bible: persiste entre sesiones, pero nunca se exporta.
Todo lo que está **desde `<!-- EXPORT-START -->` en adelante** es el guion
real, formateado según `reference/format-guide.md`, y es lo único que se
convierte a `.docx` cuando el libretista lo pide (ver "Exportar a .docx"
más abajo).

`<show-slug>` es el título en minúsculas, sin acentos, con guiones en vez
de espacios (ej. "El Motociclista Mafioso" → `el-motociclista-mafioso`).

## Etapa 0 — Setup

En cuanto haya un título provisional (de la pregunta 1, o de lo que se
haya acordado juntos), calcula el `<show-slug>` y revisa si
`guiones/<show-slug>/guion.md` ya existe. Si existe, léelo y pregunta si
el libretista quiere retomar ese show donde quedó (en vez de responder las
preguntas de Etapa 0 de nuevo) — **nunca sobrescribas un `guion.md`
existente sin confirmación explícita** de que sí se quiere empezar de
cero.

Para un show nuevo, haz estas preguntas una por una, esperando la
respuesta del libretista antes de pasar a la siguiente:

1. "¿Ya tienes un título provisional, o lo definimos juntos sobre la
   marcha?"
2. "¿Cuál es el universo o género de esta historia?" (si el libretista no
   tiene idea, ofrece ejemplos reales del género: venganza/herencia
   familiar, romance imposible, mafia y redención, sobrenatural, drama
   médico/secretos de familia.)
3. "¿Cuántos capítulos tienes en mente? Lo típico en Idilio son 45-72. El
   capítulo 11 es donde empieza el muro de pago, así que el capítulo 10 va
   a necesitar un cliffhanger especialmente fuerte — lo tendremos en cuenta
   más adelante." Si el libretista elige **menos de 10 capítulos** (por
   ejemplo, para una prueba o un show corto), de ahí en adelante toda
   referencia a "capítulo 10" en el resto de esta skill (panel de review
   automático, muro de pago) se refiere en cambio al **último capítulo**
   del show — el capítulo especial siempre es el último antes del final o
   del muro de pago, no literalmente el número 10 cuando hay menos.
4. "¿Partes de una idea que ya tienes (aunque sea suelta), o empezamos
   totalmente desde cero?"

Con las cuatro respuestas, crea `guiones/<show-slug>/guion.md` con:

- El título y la sección `## Universo` ya llenos.
- Una sección `## Setup (uso interno — no se exporta)` con la cantidad de
  capítulos planeada y un resumen de la idea inicial (o "desde cero" si no
  había una) — así estas dos respuestas quedan registradas y no se pierden
  entre sesiones.
- Las secciones `## Plot Argumental`, `## Personajes`, `## Estructura de 12
  Pasos / Giros / Climax (uso interno — no se exporta)` presentes pero
  vacías, seguidas del marcador `<!-- EXPORT-START -->` en su propia línea
  al final del archivo.

## Etapa 1 — Personaje y premisa

Antes de generar alternativas, haz estas preguntas una por una, esperando
la respuesta antes de pasar a la siguiente:

- "¿Quién sufre más en este universo? ¿Quién tiene más que perder?"
- "¿De quién quieres que el público se enamore, o con quién quieres que
  sufra?"
- "¿Ya tienes una idea de si el protagonista es más víctima, más
  protector, o ambos a la vez?"

Con esas respuestas, carga `reference/brooks-theory.md` y despacha **3
subagentes en paralelo** con el `Agent` tool (3 llamadas en un solo
mensaje, `run_in_background: false`), cada uno con este prompt (sustituye
`{universo}` y `{respuestas}` por lo que dijo el libretista):

```text
Eres guionista de melodrama para shows verticales cortos. Universo:
{universo}. Contexto adicional del libretista: {respuestas}.

Propón UN protagonista distinto para este universo. Devuelve:
1. Nombre y una línea de descripción.
2. Propósito central (qué quiere lograr).
3. Obstáculo/antagonista central (qué o quién se lo impide).
4. Por qué este personaje es la mejor puerta de entrada al "oculto moral"
   de esta historia (una virtud real pero inicialmente invisible o sin
   pruebas, que el público debe llegar a ver demostrada).

No escribas escenas todavía, solo la propuesta de personaje.
```

Presenta las 3 propuestas lado a lado. Pregunta: "¿Cuál de estos tres
personajes quieres seguir, o quieres combinar elementos de varios?".
Escribe el resultado elegido en la sección `## Personajes` de `guion.md`
(nombre, propósito, obstáculo).

## Etapa 2 — Argumento y hook

Haz estas preguntas una por una, esperando la respuesta antes de pasar a
la siguiente:

- "¿Cuál es el conflicto melodramático central? Piensa en un propósito
  amoroso: ¿qué amor se busca, se protege, o se pierde?"
- "¿Quién es el villano y qué necesita conseguir para ganar?"
- "¿Qué necesita ver o saber el público que el protagonista todavía no
  sabe (o al revés)?"

Despacha **3 subagentes en paralelo** (mismo mecanismo que la Etapa 1), con
este prompt:

```text
Eres guionista de melodrama para shows verticales cortos, estilo Idilio.
Universo: {universo}. Protagonista: {personaje_elegido}. Contexto del
libretista: {respuestas}.

Escribe:
1. PLOT ARGUMENTAL: un párrafo de 60-120 palabras presentando al
   protagonista, su propósito amoroso central, y el obstáculo/villano.
   Cierra opcionalmente con una pregunta retórica tipo gancho (ej. "¿Podrá
   X lograr Y, o Z se lo impedirá?"). Sigue el tono de una sinopsis de
   telenovela.
2. HOOK DE ARRANQUE: 1-2 líneas describiendo la primera imagen o línea de
   diálogo del capítulo 1, diseñada para que nadie abandone en los
   primeros segundos.
```

Presenta las 3 alternativas. Pregunta: "¿Cuál de estos plot argumental +
hook te convence más, o quieres que mezclemos partes de cada uno?". Escribe
el resultado elegido/editado en la sección `## Plot Argumental` de
`guion.md`.

## Etapa 3 — Reparto y polarización moral

Haz estas preguntas una por una, esperando la respuesta antes de pasar a
la siguiente:

- "¿Quién protege al protagonista?"
- "¿El villano tiene algún gesto o rasgo que lo delate ante el público,
  aunque los demás personajes todavía no lo vean?" (esto es el "cuerpo
  como prueba" de `reference/brooks-theory.md` — explícaselo brevemente si
  el libretista no está familiarizado.)
- "¿Hay algún falso aliado — alguien que parece bueno pero no lo es, o al
  revés?"

No hace falta despachar subagentes aquí por defecto. Si el libretista pide
explícitamente alternativas de villano o aliado, ofrece 2-3 propuestas (un
solo agente por propuesta, o generadas directamente por ti si son
variaciones menores).

Al terminar, escribe el reparto completo en `## Personajes` de `guion.md`.
Para cada personaje, anota explícitamente si es claramente bueno o
claramente malo, y cuál es el gesto o rasgo que lo delata (ver
`reference/brooks-theory.md`, punto de polarización moral).

## Etapa 4 — Estructura de 12 pasos

Carga `reference/structure-12-pasos.md`. Pregunta, paso a paso (uno a la
vez, sin adelantarte a los siguientes), qué ocurre en esta historia
concreta en cada uno de los 12 pasos. Al terminar deben quedar definidos
explícitamente:

- La **cuestión central** de la historia (la pregunta que sostiene todo,
  normalmente ligada al propósito y al obstáculo elegidos en las Etapas 1
  y 2).
- Un placeholder para 2-3 giros dramáticos y el clímax/desenlace — se
  desarrollan con detalle en la Etapa 5, no los inventes todavía aquí.

Escribe el resultado en la sección `## Estructura de 12 Pasos / Giros /
Climax (uso interno — no se exporta)` de `guion.md`.

## Etapa 5 — Giros y climax

Haz estas preguntas una por una, esperando la respuesta antes de pasar a
la siguiente:

- "¿Qué información oculta, cuando se revele, debe cambiarlo todo?"
- "¿Cómo se resuelve todo al final — quién gana, qué se restituye?"

Despacha **2-3 subagentes en paralelo** (`Agent` tool, un solo mensaje,
`run_in_background: false`), cada uno con este prompt (sustituye
`{resumen}` por universo + personaje + plot argumental + reparto +
cuestión central definidos hasta ahora):

```text
Eres guionista de melodrama. Historia hasta ahora: {resumen}.

Propón UN paquete de 2-3 giros dramáticos + clímax + desenlace. Cada giro
debe ser una revelación o coincidencia que se sienta ganada, no forzada
(evita que dependa solo de que un personaje sea distraído o tonto). El
clímax debe incluir al menos un momento de "tableau": los personajes se
congelan en una imagen que hace visible, sin ambigüedad, quién es inocente
y quién es culpable. El desenlace debe restituir el orden moral: la virtud
reconocida públicamente, el villano desenmascarado.
```

Presenta las alternativas, el libretista elige o combina. Escribe el
resultado final en `## Estructura de 12 Pasos / Giros / Climax`,
reemplazando el placeholder de la Etapa 4.

## Etapa 6 — Escritura por capítulo

Para cada capítulo, en orden:

1. Pregunta su objetivo dramático ("¿qué se revela o qué avanza en este
   capítulo?") y qué debe lograr específicamente su gancho de cierre.
2. Si el libretista pide alternativas para una escena o un diálogo puntual,
   carga `reference/format-guide.md` y despacha **2-3 subagentes en
   paralelo** con este prompt:

   ```text
   Eres guionista de melodrama para shows verticales, estilo Idilio. Formato
   exacto a seguir: {resumen de reference/format-guide.md}. Contexto de la
   historia: {resumen: universo, personaje, plot argumental, capítulo actual
   y su objetivo dramático}.

   Escribe esta escena/diálogo: {descripción específica pedida por el
   libretista}. Si es la última escena del capítulo, debe terminar en un
   gancho o cliffhanger — nunca en una nota resuelta o plana.
   ```

3. Antes de anexar nada, lee `guion.md` y revisa si ya existe un
   encabezado `CAPÍTULO N` para este número — puede pasar si la sesión se
   retoma o si un paso se repite por error. Si ya existe, **no lo
   dupliques**: pregunta al libretista si quiere reemplazar ese capítulo o
   si se equivocaron de número. Si lo reemplazas y el nuevo texto tiene una
   cantidad distinta de escenas que el original, **renumera también las
   escenas de todos los capítulos siguientes** para mantener la numeración
   continua — nunca dejes huecos ni números de escena repetidos. Solo
   cuando el capítulo N no existe todavía, anexa el texto aprobado (elegido,
   editado, o escrito directamente si no se pidieron alternativas) a
   `guion.md` **después** del marcador `<!-- EXPORT-START -->`, siguiendo
   el formato exacto de `reference/format-guide.md` y preservando la
   numeración continua de escenas. Todo capítulo termina en
   gancho/cliffhanger — nunca en una nota resuelta o plana.
4. Recuerda: el número de `CAPÍTULO` en el guion es 1:1 con el
   `episode_number` de las métricas de producción (ver
   `reference/format-guide.md`) — capítulo 1 es donde se juega el hook,
   capítulo 10 es el último antes del muro de pago y donde se juega el
   cliffhanger más importante.
5. Al terminar de escribir el capítulo 1 o el capítulo 10, dispara
   automáticamente el review de panel completo (ver "Review de guion" más
   abajo) antes de seguir con el siguiente capítulo.

## Exportar a .docx

Cuando el libretista lo pida: toma el contenido de `guion.md` desde
`<!-- EXPORT-START -->` en adelante (nunca el material de desarrollo de
arriba del marcador), e invoca la skill `anthropic-skills:docx` para
generar `guiones/<show-slug>/guion.docx` — un script docx-js de un solo
uso, replicando el layout descrito en `reference/format-guide.md` (título,
capítulos, escenas, diálogos). No mantengas un script de exportación
persistido en este repositorio; cada exportación es un script docx-js de un
solo uso construido en el momento.

## Review de guion

Antes de despachar cualquier review, carga `reference/format-guide.md`
(contiene la rúbrica exacta de hook/cliffhanger) y
`reference/review-report-template.html` (el formato de salida).

### Criterios (cada uno, score 1-10 + justificación de 1-2 líneas)

1. **Hook** — fuerza del gancho de apertura. Crítico en el capítulo 1.
2. **Cliffhanger** — fuerza del gancho de cierre. Crítico en el capítulo
   10, justo antes del muro de pago del capítulo 11.
3. Polarización moral clara.
4. Oculto moral / providencia narrativa.
5. Cuerpo y gesto como prueba.
6. Ritmo y formato vertical.

### Cuándo se dispara

- **Capítulo 1 y capítulo 10**: automático, apenas el libretista aprueba
  el texto. Dispara el **panel completo** (ver abajo).
- **Cualquier otro capítulo, si el libretista lo pide explícitamente**
  ("revisa el capítulo N"): también el **panel completo** — un pedido
  explícito señala que ese capítulo importa tanto como el 1 o el 10.
- **El resto de los capítulos** (2-9, 11+), revisados **en lote**: el
  review en lote solo arranca **después** de que el libretista dé signoff
  explícito ("apruebo", "sigamos", "está bien así", o equivalente) sobre
  los reviews de capítulo 1 y capítulo 10. No lo dispares antes de ese
  signoff.
- El libretista también puede pedir "revisa todo el guion" en cualquier
  momento — pedirlo explícitamente ya es el consentimiento, así que esto sí
  puede saltarse la espera del signoff normal. Pero dentro de ese barrido,
  los capítulos 1 y 10 **siguen recibiendo el panel completo de 3
  agentes**, nunca el agente único de lote — igual que si se hubieran
  pedido individualmente. Solo los capítulos que no son el 1 ni el 10 usan
  el agente único dentro de este barrido.

### Panel completo (capítulo 1, capítulo 10, o cualquier capítulo pedido explícitamente)

**3 subagentes en paralelo** (`Agent` tool, un solo mensaje,
`run_in_background: false`), cada uno evaluando un par de criterios sobre
el mismo capítulo:

- **Agente A**: Hook + Cliffhanger.
- **Agente B**: Polarización moral clara + Oculto moral/providencia
  narrativa.
- **Agente C**: Cuerpo y gesto como prueba + Ritmo y formato vertical.

Prompt del Agente A (B y C son análogos, sustituyendo los criterios y
quitando la sección de rúbrica de hook/cliffhanger que no les aplica):

```text
Eres editor de guion especializado en retención de shows verticales. Vas a
evaluar el HOOK (apertura) y el CLIFFHANGER (cierre) del siguiente
capítulo. Usa esta rúbrica exacta:

HOOK: el hook_score real se mide como el % de audiencia que pasa el primer
15% del episodio sin abandonar. Un buen hook establece stakes/emoción
claros de inmediato, sin escenas de puro trámite antes de que algo
importe. Evalúa 1-10 qué tan bien el capítulo logra esto en su(s)
primera(s) escena(s), y justifica en 1-2 líneas.

CLIFFHANGER: clasifica el cierre del capítulo con esta taxonomía exacta
(la misma que usa Idilio en producción):
- cliffhanger_type: uno de [reveal, danger, decision, confrontation,
  arrival, discovery, romantic_tension, betrayal, other]
- information_asymmetry: uno de [viewer_ahead, character_ahead, neither]
- emotional_intensity: entero 1-5
- stakes_clarity: entero 1-5
- cuts_mid_action: true/false (¿corta a media escena/frase, o cierra en
  una línea final limpia?)
Luego convierte esa clasificación en un score 1-10 + justificación de 1-2
líneas. No saltes directo al número sin clasificar primero.

Para cada criterio, si el score es menor a 8, incluye una sugerencia de
reescritura CONCRETA (el texto real sugerido, no una nota genérica como
"mejora esto").

Capítulo a evaluar:
{texto_del_capitulo}
```

Consolida los 3 outputs en un solo reporte
`guiones/<show-slug>/review-cap<N>.html`, siguiendo la estructura de
`reference/review-report-template.html`.

### Review en lote (resto de capítulos, tras signoff)

Para un show de 45-72 capítulos, mandarle **todos** los capítulos
pendientes a un solo agente de una sola vez no es confiable — el texto
combinado de 50-60 capítulos puede superar lo que un agente puede leer y
responder bien en una sola pasada, y arriesga scores/sugerencias
incompletos o de peor calidad para los últimos capítulos del lote.

En vez de eso: **parte los capítulos pendientes en lotes de máximo 12
capítulos** y despacha **un agente por lote, todos en paralelo** (`Agent`
tool, todas las llamadas en un solo mensaje, `run_in_background: false`).
Sigue siendo mucho más liviano que el panel completo — un agente por lote
de hasta 12 capítulos, no 3 agentes por capítulo. Cada agente recibe los
mismos 6 criterios y la misma rúbrica de hook/cliffhanger que el panel, y
evalúa solo los capítulos de su propio lote, devolviendo **los 6
resultados por capítulo** (uno por criterio — Hook, Cliffhanger,
Polarización moral clara, Oculto moral/providencia narrativa, Cuerpo y
gesto como prueba, Ritmo y formato vertical — cada uno con su score,
justificación, y sugerencia cuando el score sea menor a 8), igual que el
panel completo — nunca un solo score agregado por capítulo, y nunca un
resumen del lote entero. Consolida los resultados de todos los lotes en un
único
`guiones/<show-slug>/review-batch.html`.

### Salida (todas las modalidades)

Un HTML autocontenido siguiendo exactamente
`reference/review-report-template.html`: una tarjeta o fila por
capítulo/criterio con su score y justificación, y junto a cada sugerencia
un botón "Copiar sugerencia" (`navigator.clipboard.writeText`, sin
servidor, sin build). El libretista pega la sugerencia copiada en el chat
para que se aplique a `guion.md`.

`guion.md` **nunca** se anota inline con scores o sugerencias — el HTML es
la única fuente de verdad del review, para que no queden dos copias del
mismo feedback desincronizándose.

**No hay conexión en vivo a Redshift ni a las marts de `idilio-marts`.**
La rúbrica de hook_score/cliffhanger_score y la taxonomía de cliffhanger
están fijas como texto en `reference/format-guide.md`, tomadas de PR #40 al
momento de construir esta skill — el review nunca ejecuta una query.
