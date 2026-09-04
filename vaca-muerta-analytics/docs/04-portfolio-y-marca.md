# Cómo convertir esto en una pieza de portfolio (y en material para tu marca)

Tenés dos objetivos que **no** se sirven con el mismo material:

| Objetivo | Quién lo mira | Qué busca |
|---|---|---|
| **Entrar a la industria de hidrocarburos** | Un jefe de reservorios, un data lead de una operadora, un reclutador técnico | ¿Entiende el negocio? ¿Sabe de dónde salen los datos? ¿Se puede confiar en sus números? |
| **Tu marca de automatización** | Un dueño de PyME | ¿Esto me resuelve un problema? ¿Cuánto tiempo me ahorra? |

El mismo proyecto sirve para los dos, pero **contado distinto**. No intentes un
solo relato para ambos: quedás ambiguo para los dos.

---

## Para conseguir trabajo en el sector

### Lo que realmente te evalúan

En orden de peso real:

1. **¿Entendés el negocio?** — Un analista que sabe qué es el EUR y por qué
   importa vale más que uno que ajusta mejor una curva. Tu ventaja rara es que
   vas a estudiar Petróleo y Gas: **usá el vocabulario del sector con precisión**.
2. **¿Se puede confiar en tus números?** — Validación, límites declarados,
   supuestos explícitos. Un análisis que dice *"esto no aplica a pozos con menos
   de 9 meses"* es más creíble que uno que promete todo.
3. **¿Sabés de dónde salen los datos?** — Que hayas manejado el detalle del `tef`
   demuestra que trabajaste los datos de verdad, no que bajaste un CSV limpio de
   Kaggle.
4. **¿Es código o es un notebook?** — Módulos, tests y un pipeline reproducible
   te ponen en otra categoría.

### Estructura del README (el 90% de la gente solo lee esto)

```markdown
# Vaca Muerta Analytics
Curvas de declinación y estimación de EUR de pozos no convencionales,
a partir de datos públicos de la Secretaría de Energía.

🔗 [Ver el dashboard en vivo](URL)      ← ARRIBA DE TODO, antes que nada

![captura](docs/img/dashboard.png)      ← una imagen, inmediatamente

## Qué responde
- ¿Cuánto va a producir un pozo en toda su vida? (EUR)
- ¿Qué operadora perfora mejores pozos, corrigiendo por antigüedad?
- ¿Cómo se compara un bloque contra otro?

## Metodología
Arps hiperbólica modificada, con corte terminal al 6% anual...
[3-4 párrafos: qué modelo, por qué ese, qué supuestos]

## Validación
El EUR mediano estimado es X Mbbl. Las operadoras reportan Y para
pozos comparables. La diferencia se explica por Z.
[EL DIFERENCIADOR. Casi nadie valida.]

## Limitaciones
- Los últimos 2 meses de datos están incompletos.
- El modelo no aplica a pozos con menos de 9 meses de historia.
- No se corrige por longitud de rama lateral (pendiente).
[Declarar límites SUMA credibilidad, no la resta.]

## Stack y estructura
[árbol del proyecto en 10 líneas]

## Cómo correrlo
[4 comandos]
```

### Los cuatro errores que matan un proyecto de portfolio

1. **No tener demo en vivo.** Nadie va a clonar tu repo. Sin URL pública, el
   proyecto casi no existe.
2. **Un notebook de 900 celdas.** Sirve para explorar, no para mostrar.
3. **No declarar limitaciones.** Un proyecto sin límites declarados parece de
   alguien que no sabe dónde están.
4. **No poder explicar tu propio código.** Ver la advertencia en `docs/03`.

### Preparate estas preguntas

- *"¿Por qué Arps y no un modelo de machine learning?"*
  → Interpretable, es el estándar de la industria, es auditable, y con pocos
  puntos por pozo un modelo complejo sobreajusta. Además, una operadora necesita
  poder defender el número ante un auditor de reservas.
- *"¿Qué hacés con un pozo con R² bajo?"*
  → Lo marco y lo excluyo de los agregados. Suele ser un pozo con paradas largas
  o una intervención: Arps no describe eso y forzar el ajuste ensucia el
  promedio.
- *"¿Cómo sabés que tu EUR es razonable?"*
  → Lo comparo contra lo reportado por las operadoras para pozos comparables.
- *"¿Qué harías con más tiempo?"*
  → Normalizar por longitud de rama lateral con el dataset de fractura, que es
  el principal factor de confusión que hoy no corrijo.

**Esa última respuesta es la más importante de todas**: mostrar que sabés cuál es
la debilidad de tu propio trabajo es la señal de criterio más fuerte que podés dar.

---

## Para tu marca de automatización

Acá el proyecto se cuenta al revés. Al dueño de PyME **no le importa** Vaca
Muerta ni Arps. Le importa esto:

> *"Armé un sistema que todos los meses baja datos de un organismo público, los
> procesa, detecta desvíos y manda un reporte solo. Nadie toca nada. Lo mismo
> hago con los datos de tu negocio."*

**El caso de uso concreto que vendés no es petróleo: es la mecánica.**
Monitoreo automático de una fuente de datos → detección de anomalías → reporte.
Eso aplica a ventas, stock, cobranzas o producción de cualquier rubro.

### Contenido que sale de este proyecto

| Formato | Idea |
|---|---|
| **Post técnico** | "Analicé 3.000 pozos de Vaca Muerta con datos públicos. Esto encontré." Un hallazgo concreto, un gráfico, sin jerga. |
| **Video de 60 s** | El workflow de n8n corriendo: se dispara, procesa, llega el mensaje a Telegram. |
| **Post de proceso** | "El error que casi arruina mi análisis": el tema del `tef`. Los posts de errores rinden mejor que los de logros. |
| **Caso de uso** | "Cómo el mismo sistema que monitorea pozos puede monitorear tus ventas." |

**Regla:** un hallazgo concreto vale más que una descripción del proyecto.
"Encontré que los pozos del bloque X producen 40% más que el promedio, y no es
por la roca sino porque son 800 m más largos" es un post. "Hice un dashboard de
Vaca Muerta" no lo es.

---

## Cómo encaja en tu portfolio actual

Tu repo hoy tiene EchoNotes (React), la landing, dashboards y automatizaciones
con n8n. **No hay nada de Python ni de análisis de datos.** Este proyecto:

- Es tu primera pieza de **analista de datos** propiamente dicha.
- Es la única con **tests y pipeline reproducible**, lo que sube el piso técnico
  percibido de todo el portfolio.
- Conecta con tu plan de carrera de forma verificable: no decís *"me interesa el
  sector energético"*, lo mostrás.

**Ponelo primero en la tabla del README del portfolio.** Es el que mejor te
representa para donde querés ir.

---

## Una recomendación sobre el orden de las cosas

Vas a tener la tentación de seguir agregando features. Resistila. El orden que
más te conviene es:

1. Que funcione con datos reales.
2. Que esté publicado con URL.
3. Que puedas explicarlo entero.
4. **Recién ahí**, agregar features.

Un proyecto publicado y bien explicado te consigue entrevistas. Uno perfecto en
tu máquina no consigue nada.
