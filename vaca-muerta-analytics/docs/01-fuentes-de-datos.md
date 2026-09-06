# Fuentes de datos públicas de hidrocarburos (Argentina + contexto)

> **Advertencia honesta sobre este documento:** los identificadores (*slugs*) de los
> datasets están escritos de memoria y el portal ocasionalmente los renombra.
> **No los des por buenos: verificalos** antes de construir encima. El proyecto trae
> un comando para eso:
>
> ```bash
> python scripts/descargar_datos.py --buscar "no convencional"
> python scripts/descargar_datos.py --dataset no_convencional --listar
> ```
>
> El primero busca en el portal por texto libre y te devuelve los slugs reales.
> El segundo lista los archivos de un dataset sin descargarlos.

---

## 1. Secretaría de Energía de la Nación — `datos.energia.gob.ar`

**La fuente principal, y por lejos la mejor de la región.** Corre sobre CKAN
(el software estándar de portales de datos abiertos), expone una **API REST
pública sin API key ni registro**, y publica datos **pozo por pozo, mes a mes**.
Esto último es lo excepcional: la mayoría de los países publica agregados por
cuenca. Argentina publica el detalle de cada pozo, con su operadora, su
formación y su producción mensual.

### Cómo funciona la API

Tres endpoints alcanzan para todo:

| Endpoint | Para qué |
|---|---|
| `/api/3/action/package_search?q=<texto>` | Buscar datasets por texto |
| `/api/3/action/package_show?id=<slug>` | Ver un dataset y sus archivos descargables |
| URL directa del recurso | Bajar el CSV |

Probalo en el navegador, sin código:
`https://datos.energia.gob.ar/api/3/action/package_search?q=no+convencional`

En este proyecto todo eso está encapsulado en `src/petro/ingesta.py`.

### Los datasets que importan

| Qué es | Por qué te sirve | Frecuencia |
|---|---|---|
| **Producción de pozos — no convencional** | ⭐ El corazón de este proyecto. Producción mensual de cada pozo de shale/tight. Sin él no hay curvas de declinación. | Mensual |
| **Producción de pozos — por concesión (convencional)** | Comparar shale contra convencional; ver la declinación de los campos maduros del Golfo San Jorge. | Mensual |
| **Datos de fractura (Anexo IV)** | 🔥 El dataset más subestimado. Trae **etapas de fractura, arena y agua inyectada, longitud de rama lateral** por pozo. Permite responder *"¿por qué este pozo produce más?"* — que es la pregunta que realmente importa. | Diaria/mensual |
| **Perforación y terminación de pozos** | Actividad: cuántos pozos se perforan por mes. Es la variable que se cruza con el precio del crudo. | Mensual |
| **Reservas de petróleo y gas** | Reservas comprobadas por empresa y área, declaración anual. | Anual |
| **Precios de crudo (Res. 1104)** | Precio de venta interno del crudo por calidad (Medanito, Escalante). Clave: el precio local argentino **no** sigue al Brent 1 a 1. | Mensual |
| **Ventas de combustibles** | Demanda por provincia, empresa y producto. Sirve para análisis de *downstream*. | Mensual |

### Advertencias sobre estos datos (esto es lo que separa un análisis serio de uno ingenuo)

1. **`tef` es el campo más importante y el que todos ignoran.** Es el *tiempo
   efectivo de fluencia*: los días del mes en que el pozo realmente produjo. El
   caudal diario es `prod_pet / tef`, **no** `prod_pet / 30`. Un pozo que produjo
   3.000 m³ en 10 días tiene un caudal de 300 m³/d, no de 100. Si dividís por 30,
   toda tu curva de declinación está mal y vas a confundir paradas operativas con
   declinación real. En este proyecto lo maneja `limpieza.normalizar()`.

2. **Las unidades no son las de la industria internacional.** El portal usa
   **m³** para petróleo y **Mm³ (miles de m³)** para gas. La industria habla en
   **barriles** y **millones de pies cúbicos**. Si presentás resultados en m³ en
   una entrevista, se nota que no manejás el vocabulario. Conversión:
   `1 m³ = 6,28981 bbl`.

3. **Los datos se rectifican hacia atrás.** Las empresas corrigen declaraciones
   de meses anteriores (hay un campo `rectificado`). Un mismo mes puede cambiar
   entre dos descargas. Si automatizás la ingesta, **no** asumas que el pasado es
   inmutable: recargá una ventana de los últimos ~6 meses en cada corrida.

4. **Los últimos 1-2 meses están incompletos.** Siempre. No los uses para
   concluir "cayó la producción".

5. **Las operadoras cambian de nombre y se fusionan.** ExxonMobil vendió sus
   activos, Vista cambió de razón social, etc. Un análisis por operadora a lo
   largo de 8 años necesita una tabla de normalización de nombres si querés
   series consistentes.

---

## 2. IAPG — Instituto Argentino del Petróleo y del Gas

`iapg.org.ar` — **No tiene API.** Publica estadísticas en Excel y PDF.

Su valor no son los datos crudos (que salen del mismo lugar oficial), sino el
**contexto y la nomenclatura del sector**: qué se considera una cuenca, cómo se
clasifican los recursos, glosarios. Para vos, que estás entrando al sector, el
IAPG vale más como **material de estudio y de vocabulario** que como fuente de
datos. Ese vocabulario es exactamente lo que te van a escuchar en una entrevista.

---

## 3. Provincias

Neuquén, Río Negro, Mendoza y Chubut publican datos propios de concesiones,
regalías y permisos. **La provincia de Neuquén es la más completa** y a veces
tiene información de bloques y titularidad más actualizada que Nación.

Utilidad para vos: cruzar producción con **titularidad de bloques y regalías**,
que es un ángulo que casi nadie analiza porque requiere juntar dos fuentes.

---

## 4. EIA (Estados Unidos) — contexto internacional

`api.eia.gov` — API REST, **key gratuita** en
<https://www.eia.gov/opendata/register.php>.

Series útiles:

| Serie | Qué es |
|---|---|
| `PET.RWTC.M` | WTI Cushing, promedio mensual, USD/bbl |
| `PET.RBRTE.M` | Brent, promedio mensual, USD/bbl |
| `NG.RNGWHHD.M` | Henry Hub (gas), USD/MMBtu |

Además, la EIA publica el **Drilling Productivity Report** con datos de Permian
y Eagle Ford. Eso te permite un análisis que suma muchísimo:
**comparar la productividad de un pozo de Vaca Muerta contra uno de Permian**.
Es la comparación que hace todo el mundo en la industria, y tenerla hecha con
tus propios datos es una carta fuerte.

Implementado en `ingesta.precios_crudo_eia()`.

---

## 5. Otras fuentes que conviene conocer

| Fuente | Qué aporta |
|---|---|
| **ENARGAS** | Transporte y distribución de gas, capacidad de gasoductos. Relevante porque en Vaca Muerta la restricción no siempre es el subsuelo: es la evacuación. |
| **MEGSA / MATBA-ROFEX** | Precio spot del gas en el mercado local. |
| **Balances de la CNV** | Estados contables de las operadoras que cotizan (YPF, Vista, PAE). Cruzar producción con CAPEX es un análisis de nivel alto. |
| **Rystad, Wood Mackenzie, S&P** | Los estándares de la industria. **Pagos y caros.** Mencionalos para mostrar que sabés que existen; no los necesitás para este proyecto. |

---

## Resumen: por dónde empezar

Para el MVP alcanza con **una sola fuente**: el dataset de producción no
convencional de `datos.energia.gob.ar`. Todo lo demás es expansión.

```bash
python scripts/descargar_datos.py --buscar "no convencional"   # verificar el slug
python scripts/descargar_datos.py --dataset no_convencional    # descargar
python scripts/preparar_datos.py                               # procesar
streamlit run app/dashboard.py                                 # ver
```
