# Qué análisis tienen valor real (y cuáles son decorativos)

Este documento existe porque la trampa más común en un proyecto de datos de
portfolio es hacer **análisis que se ven lindos pero que nadie de la industria
pediría**. Un gráfico de barras de producción por provincia es correcto, pero no
demuestra nada: cualquiera lo hace en Excel en diez minutos.

El criterio para separar lo valioso de lo decorativo es simple:

> **¿Este análisis responde una pregunta sobre la que alguien toma una decisión
> de plata?**

---

## Nivel 1 — Mesa de entrada (necesarios, pero no te diferencian)

| Análisis | Pregunta que responde | Por qué no alcanza |
|---|---|---|
| Producción mensual por cuenca/provincia | ¿Cuánto se produce y dónde? | Está publicado en cualquier informe. |
| Ranking de operadoras | ¿Quién produce más? | Descriptivo puro. |
| Evolución de pozos activos | ¿Cuánta actividad hay? | Es un conteo. |

**Hacelos igual** — son el contexto de tu dashboard y demuestran que sabés
manipular los datos. Pero no son el gancho. En este proyecto viven en la pestaña
"Panorama", deliberadamente **no** en la primera.

---

## Nivel 2 — Donde empieza el valor real

### 2.1. Curvas de declinación y EUR ⭐ (el corazón de este proyecto)

**La pregunta:** *¿cuánto va a producir este pozo en toda su vida, y cuánto vale
entonces la inversión que se hizo para perforarlo?*

Todo el negocio del shale se reduce a esto. Un pozo de Vaca Muerta cuesta entre
10 y 15 millones de dólares. La decisión de perforarlo o no depende de una
estimación del **EUR** (*Estimated Ultimate Recovery*). Si sabés estimar un EUR
desde datos públicos, sabés hacer la cuenta central del negocio.

**Por qué te diferencia:** un analista de datos genérico grafica la serie. Un
analista que entiende el sector **ajusta Arps, reporta b y Di, y sabe explicar
por qué hace falta un corte terminal.** Esa distinción se nota en treinta
segundos de conversación.

Los tres conceptos que tenés que poder explicar sin leer:

- **qi** — el caudal al que arranca el pozo. Mide qué tan bueno salió.
- **Di** — qué tan rápido cae. En shale la caída del primer año es brutal:
  perder 60-70% del caudal inicial es lo normal, no una anomalía.
- **b** — la curvatura de la caída. `b > 1` significa que el pozo cae fuerte al
  principio pero después se aplana y produce durante años a caudal bajo. **Y acá
  está el detalle que separa a quien entendió de quien copió una fórmula:** con
  `b ≥ 1` la integral de Arps diverge, o sea que el modelo predice reservas
  infinitas. Por eso la práctica aceptada es la **hiperbólica modificada**: Arps
  hasta que la declinación instantánea baja a un valor terminal (5-10% anual), y
  de ahí en adelante exponencial. Este proyecto lo implementa así
  (`declinacion.caudal_hiperbolica_modificada`).

> Si en una entrevista te preguntan por tu proyecto y explicás **por qué cortaste
> la hiperbólica**, ya demostraste más criterio que la mayoría de los candidatos
> juniors.

### 2.2. Curvas tipo (*type curves*) y benchmarking

**La pregunta:** *¿los pozos de esta operadora/bloque son mejores que los de al
lado, o simplemente son más nuevos?*

El truco metodológico: alinear los pozos por **mes de vida**, no por fecha
calendario. Comparar la producción de enero 2026 entre dos bloques es engañoso,
porque uno puede tener pozos de tres meses y el otro de cinco años. La curva tipo
elimina ese sesgo.

Es literalmente cómo la industria compara activos. Implementado en
`declinacion.curva_tipo()`.

### 2.3. Productividad normalizada por longitud de rama lateral

**La pregunta:** *¿este pozo produce más porque la roca es mejor, o simplemente
porque es más largo?*

Un pozo de 3.000 m de rama lateral produce más que uno de 1.500 m aunque la roca
sea idéntica. La industria normaliza por metro de rama y por etapa de fractura.

**Este es el análisis con mejor relación valor/esfuerzo que podés agregar después
del MVP**, y sale del dataset de fractura (Anexo IV), que casi nadie usa.

### 2.4. Eficiencia de completación

**La pregunta:** *¿más arena y más agua producen más petróleo, o hay un punto
donde deja de rendir?*

Cruzar `arena inyectada` y `agua inyectada` contra el EUR estimado. Hay
rendimientos decrecientes y encontrar dónde están es una pregunta que las
operadoras se hacen con plata real. Requiere unir producción + fractura por
`idpozo`.

---

## Nivel 3 — Análisis que muy poca gente hace

### 3.1. Precio del crudo vs. actividad de perforación, **con rezago**

**La pregunta:** *¿cuántos meses tarda la actividad en reaccionar a un cambio de
precio?*

El error del análisis ingenuo es correlacionar precio y actividad **del mismo
mes**. No tiene sentido: una decisión de inversión tarda meses en convertirse en
un pozo perforado. Hay que correlacionar con **rezago** (lag) y buscar en qué
rezago la correlación se maximiza.

Detalle argentino importante que casi nadie contempla: **el precio interno del
crudo (Medanito) está desacoplado del Brent** por regulación, retenciones y
acuerdos de precio sostén. Analizar Vaca Muerta contra el Brent es un error
conceptual. **Mencionar esto en una entrevista es oro puro**: demuestra que
entendés el contexto regulatorio argentino, no solo la técnica.

En este proyecto: pestaña "Contexto macro", con el barrido de rezagos ya hecho.

### 3.2. Detección de anomalías operativas

**La pregunta:** *¿qué pozos se desviaron de su curva esperada este mes?*

Con la curva ajustada de cada pozo, se puede calcular el residuo del último mes
contra el modelo. Un pozo muy por debajo de su curva sugiere un problema
(falla, restricción de evacuación, intervención). Uno muy por encima sugiere una
intervención exitosa o un dato mal cargado.

**Este es tu puente natural con la automatización**, y donde tu marca y tu perfil
de analista se cruzan: es un pipeline que corre solo, detecta desvíos y avisa.
Ver `docs/05-automatizacion-n8n.md`.

### 3.3. Vaca Muerta vs. Permian

**La pregunta:** *¿cómo se compara la calidad de los pozos argentinos con los de
Estados Unidos?*

Requiere combinar datos argentinos con el Drilling Productivity Report de la EIA.
Es la comparación que hace toda la industria. Un dashboard que la tenga hecha
tiene un ángulo propio.

---

## Lo que NO conviene hacer (y por qué)

| Tentación | Por qué es mala idea |
|---|---|
| **Predecir el precio del crudo con machine learning** | Nadie puede. Un modelo de precio del petróleo en un portfolio junior lee como ingenuidad, no como habilidad. |
| **Un mapa de pozos como pieza central** | Se ve espectacular y no dice nada. Como complemento, bien. Como el análisis principal, es decoración. |
| **Deep learning para la declinación** | Arps con tres parámetros es el estándar de la industria, es interpretable y es auditable. Una red neuronal que ajusta mejor pero que no podés explicar es peor para el negocio. Además, en una entrevista te van a pedir que expliques el modelo. |
| **Dashboards con 40 gráficos** | Cinco preguntas bien respondidas superan a cuarenta gráficos sin pregunta. |

---

## El orden recomendado

| Análisis | Estado |
|---|---|
| 2.1 Curvas de declinación y EUR | ✅ construido |
| 2.2 Curvas tipo y benchmarking | ✅ construido |
| 2.3 Normalización por rama lateral | ✅ construido (`src/petro/fractura.py`) |
| **Validación por backtest** | ✅ construido (`src/petro/validacion.py`) |
| 3.2 Detección de anomalías | ✅ construido (`scripts/detectar_anomalias.py`) |
| 2.4 Eficiencia de completación (arena/agua vs EUR) | ⬜ los datos ya se descargan |
| 3.1 Precio con rezago | ⬜ requiere API key de la EIA |
| 3.3 Vaca Muerta vs Permian | ⬜ requiere el Drilling Productivity Report |

**El backtest no estaba en la lista original y terminó siendo lo más valioso.**
No es un análisis del sector: es un análisis *del modelo*. Responde la pregunta
que cualquiera va a hacer antes de mirar un solo gráfico — *¿por qué te creo?* —
y la responde con un número medido, no con una explicación de la metodología.

Si tenés que elegir una sola cosa para agregar a un proyecto de datos, agregá
la validación antes que otro análisis.
