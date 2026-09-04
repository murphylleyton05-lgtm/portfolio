# 🛢️ Vaca Muerta Analytics

**Curvas de declinación y estimación de EUR de pozos no convencionales**, a partir
de datos públicos de la Secretaría de Energía de la Nación.

> ⚠️ **Estado: MVP funcional.** Corre end-to-end con datos sintéticos incluidos y
> está listo para conectarse a los datos oficiales. Ver [Limitaciones](#limitaciones).

**Dos formas de verlo:**

| | Qué es | Cómo se abre |
|---|---|---|
| **`web/index.html`** | App web estática, sin instalar nada. Los 150 pozos y sus curvas ya calculadas van embebidos en el archivo. | Doble clic, o publicarla en Netlify |
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

## Cómo correrlo

```bash
git clone <este-repo>
cd vaca-muerta-analytics

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Opción A — con datos sintéticos** (sin descargar nada, funciona al instante):

```bash
python scripts/generar_demo.py
python scripts/preparar_datos.py
streamlit run app/dashboard.py
```

**Opción B — con datos reales** de la Secretaría de Energía:

```bash
python scripts/descargar_datos.py --buscar "no convencional"   # verificar el slug
python scripts/descargar_datos.py --dataset no_convencional    # descargar (cientos de MB)
python scripts/preparar_datos.py
streamlit run app/dashboard.py
```

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
│   └── demo_data.py              Generador sintético (para correr sin descargar)
├── scripts/
│   ├── descargar_datos.py        Descarga desde el portal oficial
│   ├── generar_demo.py           Genera el dataset sintético
│   ├── preparar_datos.py         Pipeline: crudo → procesado
│   └── detectar_anomalias.py     Pozos fuera de su curva esperada
├── app/dashboard.py              Dashboard Streamlit (5 pestañas)
├── web/index.html                App web autocontenida (abrir y listo)
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
- **No se corrige por longitud de rama lateral ni por etapas de fractura.** Es el
  principal factor de confusión pendiente: un pozo más largo produce más aunque la
  roca sea idéntica. Requiere sumar el dataset de fractura (Anexo IV).
- **El EUR asume 30 años de vida útil y 6% de declinación terminal.** Ambos son
  supuestos, configurables en `src/petro/config.py`.
- **La detección de anomalías es un detector, no un diagnóstico:** señala pozos
  para mirar, no dice qué les pasa.

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
