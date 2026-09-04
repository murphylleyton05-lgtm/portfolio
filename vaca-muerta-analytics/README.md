# 🛢️ Vaca Muerta Analytics

**Curvas de declinación y estimación de EUR de pozos no convencionales**, a partir
de datos públicos de la Secretaría de Energía de la Nación.

> ⚠️ **Estado: MVP funcional.** Corre end-to-end con datos sintéticos incluidos y
> está listo para conectarse a los datos oficiales. Ver [Limitaciones](#limitaciones).

**Dos formas de verlo:**

| | Qué es | Cómo se abre |
|---|---|---|
| **`web/index.html`** | App web estática, sin instalar nada. Los pozos y sus curvas ya calculadas van embebidos en el archivo. Se regenera con `scripts/generar_web.py`. | Doble clic, o publicarla |
| **`app/dashboard.py`** | Dashboard Streamlit, conectado al pipeline en vivo. Recalcula sobre los datos que descargues. | `streamlit run app/dashboard.py` |

La versión web es para mostrar; la de Streamlit es para trabajar.

---

## Qué preguntas responde

| Pregunta | Dónde |
|---|---|
| ¿Cuánto va a producir un pozo en toda su vida? (**EUR**) | Pestaña *Curva de declinación* |
| ¿Qué operadora perfora mejores pozos, **corrigiendo por antigüedad**? | Pestaña *Curvas tipo* |
| ¿Qué bloque tiene mejor calidad de roca? | Pestaña *Panorama* |
| ¿Cuánto tarda la actividad en reaccionar al precio del crudo? | Pestaña *Contexto macro* |
| ¿Qué pozos se salieron de su curva esperada este mes? | `scripts/detectar_anomalias.py` |
| ¿Este bloque es mejor, o sus pozos son más largos? | Pestaña *¿Es la roca o el pozo es más largo?* |
| ¿Se le puede creer al modelo? | Pestaña *¿Se le puede creer al modelo?* |

---

## Metodología

El modelo es **Arps hiperbólica modificada**, el estándar de la industria para
análisis de declinación (DCA).

**Las ecuaciones de Arps** describen el caudal `q` de un pozo en el tiempo con
tres parámetros: `qi` (caudal inicial), `Di` (declinación nominal inicial) y `b`
(exponente de declinación):

```
b = 0        exponencial   q = qi · e^(−Di·t)
0 < b < 1    hiperbólica   q = qi / (1 + b·Di·t)^(1/b)
b = 1        armónica      q = qi / (1 + Di·t)
```

**Por qué "modificada":** en shale es normal encontrar `b > 1`, y con `b ≥ 1` la
integral de Arps diverge — el modelo predice reservas infinitas. Por eso se usa
la curva hiperbólica **hasta que la declinación instantánea cae al valor terminal
(6% anual por defecto)** y de ahí en adelante se continúa con exponencial. Sin
ese corte, cualquier EUR calculado con `b ≥ 1` es inválido.

**Tres decisiones de tratamiento de datos que cambian el resultado:**

1. **El caudal se calcula sobre días efectivos de producción (`tef`), no sobre
   días del mes.** Un pozo que produjo 3.000 m³ en 10 días tiene un caudal de
   300 m³/d, no de 100. Ignorar esto convierte paradas operativas en declinación
   aparente.
2. **La serie de ajuste arranca en el pico de producción**, no en el primer mes:
   los pozos de shale tardan 1-3 meses en alcanzar su máximo por la rampa de
   puesta en marcha.
3. **Los meses con producción nula se descartan**, no se tratan como cero. Un
   cero significa "pozo parado", no "el pozo declinó a cero".

---

## Validación: ¿por qué creerle al EUR?

Un EUR es una predicción a 30 años. Cualquiera puede ajustar una curva y publicar
un número grande, así que el proyecto se valida **escondiéndole datos al modelo**:

1. Se ajusta la curva con los **primeros 24 meses** de cada pozo.
2. Se le pide predecir los 12, 24 y 36 meses siguientes.
3. Se compara con lo que el pozo **realmente produjo**.

El pozo ya produjo ese período; el modelo no lo vio. Es una predicción real, no un
ajuste sobre datos conocidos. Un pozo entra en un horizonte **solo si realmente lo
vivió**: sin esa condición, el error a 36 meses se calcularía mezclando pozos que
nunca llegaron ahí.

Se reportan tres cosas distintas, y la diferencia entre ellas es el punto:

| Métrica | Qué responde |
|---|---|
| **Error por pozo** (mediana de \|error\|) | Cuánto se equivoca en **un** pozo |
| **Sesgo** (error mediano con signo) | Si se equivoca siempre para el mismo lado |
| **Error del total** (agregado) | Cuánto se equivoca en el **conjunto** de pozos |

**El resultado sobre datos reales, en una línea:** pozo por pozo el modelo no es
preciso, y **subestima de forma sistemática**; el sesgo crece con el horizonte. En
el agregado anda bastante mejor, porque los errores individuales se compensan en
parte. Eso es información útil, no un fracaso: dice que este modelo sirve para
evaluar **un conjunto** de pozos, no para decidir sobre uno solo — que es
exactamente como se usa una curva tipo en la industria.

### Resultados de la última corrida

Este bloque lo reescribe el workflow en cada actualización, así el README nunca
queda con números viejos.

<!-- RESULTADOS:INICIO -->
> Última actualización: **2026-09-04** · datos oficiales de la Secretaría de Energía · período **2006-01 a 2026-07** · **2,613 pozos**, 2,463 con curva ajustada.

| Horizonte | Error en **un pozo** | Sesgo | Dentro de ±20% | Error en el **total** | Pozos |
|---|---:|---:|---:|---:|---:|
| 12 meses | 23.3% | -8.9% | 44% | -5.9% | 1,424 |
| 24 meses | 27.3% | -11.3% | 38% | -5.9% | 1,225 |
| 36 meses | 30.1% | -14.5% | 35% | -8.6% | 978 |

**En una línea:** a 36 meses el modelo se equivoca **30% en un pozo individual** pero solo **9% en el total** de 978 pozos — los errores se compensan. Y subestima de forma sistemática, lo que es corregible.

**Economía de pozo**: precio de equilibrio mediano de **US$ 48/bbl** (P10 30 · P90 355), sobre 1,775 pozos. A US$ 65/bbl cierra el **64%**, con un repago mediano de 16 meses. Supuestos: pozo US$ 12.0M · opex US$ 12.0/bbl · regalías 12.0% · descuento 10.0% anual. **Son supuestos, no datos medidos.**

**Normalización por rama lateral** (1,302 pozos con longitud declarada, mediana 2,514 m): la longitud explica el **6%** de la diferencia de EUR entre pozos, pero al normalizar el ranking se mueve **95 puestos** en la mediana y del top 10 por EUR crudo sobreviven solo **3**.
<!-- RESULTADOS:FIN -->

---

## Cómo correrlo

```bash
git clone <este-repo>
cd vaca-muerta-analytics

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Sin instalar nada:** pestaña **Actions** del repo → *Actualizar Vaca Muerta* →
**Run workflow**. GitHub descarga los datos oficiales, ajusta las curvas, regenera
la app y commitea el resultado. También corre solo el día 20 de cada mes, que es
cuando la Secretaría publica.

**En tu máquina**, un solo comando que hace lo mismo:

```bash
python scripts/actualizar.py            # datos REALES de la Secretaría de Energía
python scripts/actualizar.py --demo     # datos sintéticos, para probar sin descargar
```

Cuando termina, `web/index.html` queda actualizado — abrilo con doble clic.
Para el dashboard interactivo: `streamlit run app/dashboard.py`.

<details>
<summary>Los pasos por separado, si algo falla y querés mirarlo de a uno</summary>

```bash
python scripts/descargar_datos.py --buscar "no convencional"   # verificar el slug
python scripts/descargar_datos.py --dataset no_convencional    # descargar (cientos de MB)
python scripts/preparar_datos.py                               # limpiar y ajustar curvas
python scripts/generar_web.py                                  # regenerar web/index.html
```

**Los dos errores que aparecen con datos reales:**

| Síntoma | Dónde se arregla |
|---|---|
| El dataset no aparece o cambió de nombre | `DATASETS` en `src/petro/ingesta.py` — buscá el slug nuevo con `--buscar` |
| "El CSV no trae las columnas esperadas" | `COLUMNAS_OFICIALES` en `src/petro/limpieza.py` |

</details>

**Detección de anomalías:**

```bash
python scripts/detectar_anomalias.py --umbral 25
python scripts/detectar_anomalias.py --umbral 25 --json    # para n8n
```

**Tests:**

```bash
pytest -v
```

---

## Estructura

```
vaca-muerta-analytics/
├── src/petro/                    Librería del proyecto
│   ├── config.py                 Rutas y parámetros
│   ├── ingesta.py                API CKAN de datos.energia.gob.ar + EIA
│   ├── limpieza.py               Normalización del esquema oficial
│   ├── declinacion.py            ⭐ Arps, EUR, curvas tipo
│   ├── fractura.py               Normalización por rama lateral
│   ├── validacion.py             Backtest: predecir lo que el modelo no vio
│   └── demo_data.py              Generador sintético (para correr sin descargar)
├── scripts/
│   ├── actualizar.py             ⭐ Todo el pipeline en un comando
│   ├── descargar_datos.py        Descarga desde el portal oficial
│   ├── generar_demo.py           Genera el dataset sintético
│   ├── preparar_datos.py         Pipeline: crudo → procesado
│   ├── generar_web.py            Incrusta los datos en la app web
│   └── detectar_anomalias.py     Pozos fuera de su curva esperada
├── app/dashboard.py              Dashboard Streamlit (5 pestañas)
├── web/
│   ├── plantilla.html            La app, sin datos (se edita acá)
│   └── index.html                La app con los datos incrustados (generado)
├── automatizacion/               Workflow de n8n para correrlo solo
├── tests/                        23 tests
└── docs/                         Fuentes, metodología, plan, portfolio
```

**Por qué esta estructura:** la lógica vive en `src/petro/` como librería
importable; los scripts son entradas de línea de comandos delgadas; el dashboard
solo lee archivos ya procesados. El resultado es que el mismo código sirve para
el dashboard, para el flujo automatizado y para un notebook exploratorio, y todo
es testeable sin levantar Streamlit.

---

## Datos de demostración

El proyecto incluye un generador sintético (`src/petro/demo_data.py`) que produce
pozos ficticios con curvas de Arps reales más ruido operativo, paradas y rampa de
puesta en marcha. **Los pozos generados no existen.** Sirven para que la app sea
navegable sin descargar los datasets oficiales (cientos de MB) y para que los
tests sean reproducibles.

El dashboard muestra un cartel de advertencia cuando está usando datos sintéticos.
El generador emite el **mismo esquema crudo que el CSV oficial**, así que los datos
demo pasan exactamente por el mismo pipeline de limpieza que los reales.

---

## Limitaciones

Declaradas a propósito — un análisis sin límites explícitos es un análisis en el
que no conviene confiar.

- **Los últimos 1-2 meses de datos oficiales están siempre incompletos.** No usar
  para concluir que la producción cayó.
- **Las declaraciones se rectifican hacia atrás:** un mismo mes puede cambiar
  entre dos descargas.
- **El modelo no aplica a pozos con menos de 9 meses de historia útil**, ni a
  pozos con paradas largas o intervenciones (Arps no describe eso). Esos pozos se
  marcan con R² bajo y se excluyen de los agregados.
- **No se corrige por espaciamiento entre pozos ni por interferencia.** Un pozo
  perforado al lado de otro ya en producción rinde menos (efecto *parent-child*).
  Es el principal factor de confusión que queda sin corregir.
- **La declinación terminal (6% anual) y el tope de `b` en 2 son decisiones de
  modelado, no mediciones**, y el backtest sugiere que son conservadoras: el
  modelo subestima de forma sistemática, y el sesgo crece con el horizonte. Un
  tope de `b` más alto o una terminal más baja darían EUR mayores.
- **Solo se modela petróleo.** El gas se lee y se limpia, pero no se le ajusta
  curva ni se estima EUR.
- **No hay economía.** Sin precio de venta ni costo de pozo no hay VAN ni punto
  de equilibrio: el proyecto dice cuánto produce un pozo, no si conviene.
- **El EUR asume 30 años de vida útil y 6% de declinación terminal.** Ambos son
  supuestos, configurables en `src/petro/config.py`.
- **La detección de anomalías es un detector, no un diagnóstico:** señala pozos
  para mirar, no dice qué les pasa.
- **El modelo no sirve para pronosticar un pozo individual.** El backtest lo
  muestra: el error típico por pozo es alto y solo una minoría cae dentro de
  ±20%. Úsese para comparar conjuntos, no para decidir sobre un pozo suelto.
- **Los ajustes de mala calidad se excluyen de los rankings.** Cuando la curva no
  ajusta, el optimizador lleva `b` a su tope y el EUR se dispara: sin filtrar,
  los peores ajustes encabezan el ranking con EUR físicamente imposibles.

---

## Documentación

| Documento | Contenido |
|---|---|
| [Fuentes de datos](docs/01-fuentes-de-datos.md) | Qué hay disponible, cómo se accede, y las trampas de cada fuente |
| [Análisis con valor](docs/02-analisis-con-valor.md) | Qué análisis importan en el sector y cuáles son decorativos |
| [Plan de 2 semanas](docs/03-plan-2-semanas.md) | Ruta día por día de MVP a proyecto publicado |
| [Portfolio y marca](docs/04-portfolio-y-marca.md) | Cómo presentarlo para trabajo y para clientes |
| [Automatización n8n](docs/05-automatizacion-n8n.md) | De dashboard a sistema que corre solo |

---

## Stack

Python · pandas · scipy (`curve_fit`) · Streamlit · Plotly · pytest · n8n

---

**Lleyton Murphy** — Analista de datos y automatización con IA · La Plata, Argentina
