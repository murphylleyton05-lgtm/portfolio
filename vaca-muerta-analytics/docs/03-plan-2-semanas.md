# Plan de 2 semanas — de cero a proyecto mostrable

**Supuestos:** ~20 h/semana (≈40-45 h en total), Python básico sin proyectos
previos, objetivo de tener algo público y defendible en 14 días.

## Una aclaración importante antes de arrancar

En este repositorio **ya está construido el esqueleto funcional del MVP**:
ingesta, limpieza, ajuste de Arps, dashboard y tests. Podés correrlo hoy.

Eso te ahorra la parte más frustrante (pelearte con la estructura del proyecto),
pero **crea un riesgo real**: presentar como tuyo un código que no entendés. En
una entrevista técnica eso se detecta en dos preguntas y es mucho peor que
presentar algo más simple pero propio.

Por eso el plan **no** es "corré esto y subilo". Las dos primeras semanas están
diseñadas para que **entiendas cada pieza, la rompas, la arregles y la extiendas**.
El código de arranque es un andamio, no el entregable.

Regla que te propongo, y que vale más que todo lo demás de este documento:

> **No subas a tu portfolio ninguna línea que no puedas explicar en voz alta.**

---

## Semana 1 — Entender y hacerlo propio

### Día 1 (4 h) — Que funcione en tu máquina

```bash
git clone <tu-repo>
cd vaca-muerta-analytics

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scripts/generar_demo.py
python scripts/preparar_datos.py
streamlit run app/dashboard.py
```

- Navegá las cinco pestañas. Movés los filtros, mirás qué cambia.
- Corré `pytest -v` y mirá los nombres de los tests: te cuentan qué hace el
  código mejor que cualquier documentación.

**Entregable:** el dashboard corriendo en tu máquina.

**Si algo falla:** anotá el error y resolvelo. Pelearte con un entorno virtual y
un `ModuleNotFoundError` es parte del trabajo real, no una pérdida de tiempo.

### Día 2 (4 h) — Entender la matemática, no el código

Hoy no toques Python. Abrí `docs/02-analisis-con-valor.md` y `src/petro/declinacion.py`
y trabajá hasta poder responder de memoria:

1. ¿Qué significan qi, Di y b, en palabras, sin fórmulas?
2. ¿Por qué la serie de ajuste arranca en el **pico** y no en el primer mes?
3. ¿Por qué un mes con `tef = 0` se descarta en vez de tratarse como cero?
4. ¿Por qué hay que cortar la hiperbólica y pasar a exponencial?
5. ¿Qué es el EUR y por qué es el número que le importa a una operadora?

**Test de que entendiste:** explicáselo en voz alta, en 3 minutos, a alguien que
no sabe nada de petróleo. Si no podés, volvé al punto 1.

**Entregable:** tus propias notas, escritas por vos.

### Día 3 (4 h) — Bajar los datos reales

```bash
python scripts/descargar_datos.py --buscar "no convencional"
python scripts/descargar_datos.py --dataset no_convencional --listar
python scripts/descargar_datos.py --dataset no_convencional
python scripts/preparar_datos.py
```

**Es muy probable que algo falle acá**, y está perfecto: los slugs pueden haber
cambiado, o el CSV puede traer una columna con otro nombre. Arreglarlo es el
trabajo. El mapeo vive en un solo lugar: `COLUMNAS_OFICIALES` en
`src/petro/limpieza.py`.

**Entregable:** el dashboard mostrando pozos reales, sin el cartel amarillo de demo.

**Guardá capturas del error y de cómo lo resolviste.** Eso es contenido para tu
marca y material para contar en una entrevista.

### Día 4 (4 h) — Validar contra la realidad

El paso que casi nadie hace y el que más credibilidad te da.

- Buscá el EUR promedio publicado de un pozo de Vaca Muerta (informes de YPF o
  Vista, presentaciones a inversores, notas del sector).
- Compará con lo que estima tu modelo. ¿Mismo orden de magnitud?
- Elegí 5 pozos con R² bajo y mirálos uno por uno. ¿Qué tienen? ¿Paradas largas?
  ¿Intervenciones? ¿Cambio de sistema de extracción?

**Entregable:** una sección de "validación" en tu README con números concretos.
Poder decir *"mi modelo estima X y la operadora reporta Y, la diferencia se
explica por Z"* vale más que diez gráficos.

### Día 5 (4 h) — Romper y extender

Ahora sí, modificá código. Sugerencias, de menor a mayor dificultad:

1. Agregá una métrica nueva al dashboard (ej.: producción acumulada a 12 meses,
   que es el indicador estándar de la industria para comparar pozos).
2. Agregá un filtro por año de puesta en marcha.
3. Ajustá también la curva de **gas**, no solo la de petróleo.
4. Escribí un test nuevo en `tests/` para lo que agregaste.

**Entregable:** al menos un aporte tuyo, con su test.

### Días 6-7 (6-8 h) — README y primer deploy

- Escribí el README con tus palabras (ver `docs/04-portfolio-y-marca.md`).
- Deploy en **Streamlit Community Cloud** (gratis): conectás el repo de GitHub y
  te da una URL pública. Para que la demo funcione sin descargar 300 MB, la app
  ya cae automáticamente en los datos sintéticos si no hay datos reales.
- Sacá 3-4 capturas buenas para el README.

**Entregable:** URL pública funcionando. **Fin de la semana 1: ya tenés algo
mostrable.** Todo lo que sigue es mejora.

---

## Semana 2 — Profundizar y diferenciarte

### Día 8-9 (8 h) — Sumar el dataset de fractura

El mejor retorno por hora invertida de todo el proyecto.

- Descargá el dataset de fractura (Anexo IV).
- Unilo con producción por `idpozo`.
- Calculá **EUR por metro de rama lateral** y **EUR por etapa de fractura**.
- Nueva pestaña: *¿este pozo produce más por la roca o porque es más largo?*

Esto es análisis de nivel 2-3 (ver `docs/02`) y casi nadie lo hace con datos
públicos. Es tu diferencial más concreto.

### Día 10 (4 h) — Contexto macro real

- Sacá la API key gratuita de la EIA.
- Reemplazá los precios sintéticos por WTI/Brent reales.
- Sumá el precio interno del crudo (Res. 1104) y **mostrá la brecha con el
  Brent**. Ese gráfico solo ya cuenta la historia regulatoria argentina.

### Día 11-12 (8 h) — Automatización (tu marca)

Acá se cruza tu perfil de analista con tu negocio de automatización.
Ver `docs/05-automatizacion-n8n.md`.

- Workflow de n8n que corre el pipeline el día 20 de cada mes (cuando la
  Secretaría publica).
- Detección de pozos que se desviaron de su curva.
- Reporte mensual automático a Telegram/mail.

**Entregable:** un video corto de 60 segundos mostrando el flujo andando. Ese
video es contenido para LinkedIn y demo de venta para tu marca, al mismo tiempo.

### Día 13 (4 h) — Pulido

- `pytest` en verde y con cobertura de lo que agregaste.
- Que el README tenga capturas y la URL en vivo arriba de todo.
- Revisá que no haya quedado ninguna API key en el código
  (`git log -p | grep -i "api_key"`).
- Coherencia visual: títulos, unidades, decimales.

### Día 14 (4 h) — Contarlo

Esto no es opcional: un proyecto que nadie ve no sirve para conseguir trabajo.

- **Post de LinkedIn** con el hallazgo más interesante que encontraste en los
  datos reales (no una descripción del proyecto: **un hallazgo**).
- README de tu portfolio actualizado con el proyecto arriba.
- Preparate las respuestas a: *"¿por qué Arps y no un modelo de ML?"*,
  *"¿qué hacés si un pozo tiene R² bajo?"*, *"¿cómo validaste el EUR?"*

---

## Si te atrasás: qué es negociable

| Prioridad | Parte | Comentario |
|---|---|---|
| 🔴 Innegociable | Días 1-4: entender + datos reales + validación | Sin esto no hay proyecto |
| 🔴 Innegociable | Día 6-7: deploy público + README | Sin esto nadie lo ve |
| 🟡 Alta | Día 8-9: dataset de fractura | Tu mayor diferencial |
| 🟢 Negociable | Día 11-12: automatización | Sumalo después, sin culpa |
| 🟢 Negociable | Día 10: precios reales | Los sintéticos alcanzan para mostrar la mecánica |

**Un proyecto terminado al 80% y publicado vale infinitamente más que uno al
100% que sigue en tu máquina.**
