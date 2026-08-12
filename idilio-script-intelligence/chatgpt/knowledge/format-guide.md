# Guía de formato — libretos Idilio

Reglas extraídas directamente de libretos reales de Idilio (carpetas
"LIBRETOS IDILIO" y "GUIONES MICRO SERIES LARGAS" en Drive) y de cómo el
pipeline de datos de la empresa procesa esos mismos guiones
(`idilio-marts`). Seguir esto al pie de la letra al escribir un capítulo
(Etapa 6) o al hacer un review.

## Estructura del documento completo

1. Título (mayúsculas), opcionalmente género ("Melodrama"), autor y año —
   varía según el proyecto, no es obligatorio.
2. Un párrafo de "Plot Argumental" o sinopsis (ver Etapa 2 de `SKILL.md`).
3. Opcional: listado de personajes ("LISTADO DE PRESENTACIÓN DE
   PERSONAJES") con una línea de rol por personaje (Protagonista,
   Antagonista, etc.).
4. Los capítulos, en orden, cada uno con sus escenas.

## Capítulos = episodios

**`CAPÍTULO N` en el guion es exactamente `episode_number` N en las
métricas de producción.** El pipeline que carga los guiones a Redshift
(`scripts/load_episode_scripts.py` en `idilio-marts`) reconoce como
encabezado de capítulo una línea completa en cursiva Markdown como
"*Capítulo 1*" — sin distinguir mayúsculas de minúsculas, aceptando
"Capitulo" sin tilde y números con ceros a la izquierda ("*Capítulo 01*").
El loader rechaza números de capítulo duplicados y un conteo de capítulos
que no coincida con lo esperado, pero **sí permite saltos en la
numeración y no exige que empiece en el capítulo 1** — igual, para no
arriesgarse, mantén la numeración secuencial y sin huecos al escribir: un
número duplicado o un conteo que no cuadre hace que el show completo se
descarte (no solo el episodio con el problema) aguas abajo.

Esto es lo que hace que el capítulo 1 y el capítulo 10 sean especiales:

- **Capítulo 1** = primer episodio → mide `hook_score`.
- **Capítulo 10** = último episodio gratis antes de que el capítulo 11
  quede detrás del muro de pago → mide `cliffhanger_score`. Ojo: esto NO
  es una señal pura de historia — un espectador que llega al final del
  capítulo 10 y no continúa puede estar diciendo "esta historia no me
  enganchó" o simplemente "no quiero pagar", y `cliffhanger_score` no
  distingue entre las dos. Sigue siendo la señal de cliffhanger más
  importante que existe (es la única que se juega contra una decisión real
  de seguir o no), pero trátala como "voluntad de continuar, mezclada con
  precio" — no como retención de historia aislada del precio.

**Shows de menos de 10 capítulos:** "capítulo 10" arriba se refiere en
realidad al **último capítulo** del show (ver Etapa 0 de `SKILL.md`) — es
el capítulo antes del que exista un muro de pago o, si el show entero es
gratis, simplemente el capítulo de cierre. Si no hay ningún capítulo
después del último (no hay "capítulo 11" real, pagado o no), no hay
`cliffhanger_score` que medir ahí — al revisar ese capítulo, evalúa los
otros 5 criterios normalmente y trata el Cliffhanger como "¿el final deja
ganas de que hubiera más?" en vez de un score atado a un episodio
siguiente que no existe.

## Numeración de escenas

Las escenas se numeran de forma **continua a lo largo de todo el guion**,
nunca se reinician en cada capítulo. Si el capítulo 1 termina en la escena
4, el capítulo 2 empieza en la escena 5.

Formato del encabezado de escena:

```text
N. INT./EXT. LUGAR - MOMENTO DEL DÍA
```

Ejemplos reales del corpus: `1. EXT. BOSQUES CERCA DEL PALACIO GRIMWALD -
VALDEN - DÍA`, `4. INT. SALÓN - PALACIO GRIMWALD - MOMENTOS DESPUÉS`.

## Acotaciones (líneas de acción)

Por defecto, en MAYÚSCULAS — es la convención dominante en el corpus.
Deben describir acción y estado físico/emocional visible, no pensamientos
internos sin señal corporal (ver `brooks-theory.md`, punto 3: el cuerpo
como prueba).

## Diálogo

```text
NOMBRE PERSONAJE
(paréntesis opcional de actitud/tono, ej: preocupada, sollozando)
Línea de diálogo en formato normal (no en mayúsculas).
```

El nombre del personaje va en mayúsculas en su propia línea, inmediatamente
antes de su línea de diálogo.

## Cierre de capítulo

Cada capítulo **tiene** que terminar en un gancho o cliffhanger — nunca en
una nota resuelta o plana. Puede marcarse explícitamente ("FIN (EPISODIO
N)", "Final capítulo N") o simplemente terminar la última escena en el
beat de gancho sin una marca textual — cualquiera de las dos convenciones
es válida, pero debe mantenerse consistente dentro de un mismo show.

## Plot Argumental (patrón real observado)

Un párrafo de 60-120 palabras que: presenta al protagonista y su
situación inicial, introduce el propósito amoroso central, nombra el
obstáculo/villano, y opcionalmente cierra con una o dos preguntas
retóricas tipo gancho ("¿Podrá X lograr Y, o Z se lo impedirá?"). Patrón
real observado (paráfrasis, no cita textual): una protagonista pierde su
posición u hogar tras una traición familiar, es rescatada por un
desconocido con un pasado oculto, y la trama avanza entre engaños y
revelaciones hasta que la verdad y el amor derrotan a la ambición.

## Rúbrica de Hook y Cliffhanger (de `idilio-marts`, PR #40)

Estas son las definiciones **reales** que usa Idilio para medir hook y
cliffhanger con datos de audiencia (`models/marts/mart_episode_script_metrics.sql`
en `idilio-marts`, PR #40) — la skill evalúa el guion en preproducción
contra esta misma vara, aunque todavía no haya datos de audiencia de ese
show en particular.

### Hook — por qué existe: lograr que el usuario termine el episodio una vez lo empieza

`hook_score` real (0-1, continuo): para cada usuario que empezó el
episodio, se mide su progreso máximo de reproducción como fracción de un
corte del 15% inicial del episodio (capado en 1 al pasarlo), promediado
entre todos los que empezaron. Alguien que abandona al 5% pesa más
negativamente que alguien que abandona al 14%.

**En términos de escritura:** el primer ~15% del episodio (la o las
primeras escenas) es la parte que no puede darle a nadie una razón para
irse. Nada de escenas de trámite antes de que algo importe — stakes o
emoción claros desde la primera línea o imagen.

### Cliffhanger — por qué existe: lograr que el usuario quiera ver el siguiente episodio

`cliffhanger_score` real: % de usuarios que terminaron este episodio
(`playback_progress > 0.95`) que también vieron el episodio N+1.

Idilio ya clasifica los cliffhangers de episodios reales (vía la tabla
`episode_cliffhanger_features`, generada por
`scripts/extract_cliffhanger_features.py`) con esta taxonomía exacta — la
skill usa la **misma** taxonomía para que el review hable el mismo idioma
que la analítica de producción:

- **cliffhanger_type**: uno de `reveal`, `danger`, `decision`,
  `confrontation`, `arrival`, `discovery`, `romantic_tension`, `betrayal`,
  `other`.
- **information_asymmetry**: uno de `viewer_ahead` (el espectador sabe
  algo que un personaje no sabe — ironía dramática), `character_ahead` (un
  personaje descubre algo que el espectador no vio venir), `neither`.
- **emotional_intensity**: entero 1-5, qué tan cargado es el beat final.
- **stakes_clarity**: entero 1-5, qué tan claro es lo que está en juego.
- **cuts_mid_action**: booleano — ¿corta a media escena/frase, o cierra en
  una línea final limpia?

### Cómo se usa esta rúbrica en el review

Para cada capítulo revisado, clasifica primero con estos 5 campos
(cliffhanger) y evalúa el porcentaje de "sin razón para irse" en la
apertura (hook), y **solo después** convierte eso en el score final 1-10 +
justificación de 1-2 líneas que pide el sistema de review de `SKILL.md`. No
saltes directo al número sin clasificar primero.

**Nota:** esta rúbrica es texto fijo, tomado de `idilio-marts` al momento
de construir esta skill (PR #40, no fusionado al momento de escribir esta
guía). No hay conexión en vivo a Redshift ni a las marts — si esa PR
cambia en el futuro, esta guía debe actualizarse manualmente.
