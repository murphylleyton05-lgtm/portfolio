# Automatización con n8n: de dashboard a sistema que corre solo

Esta es la parte donde tu perfil de analista de datos y tu negocio de
automatización dejan de ser dos cosas separadas.

Un dashboard es **pasivo**: alguien tiene que acordarse de abrirlo. Un sistema
de monitoreo es **activo**: te avisa cuando pasa algo. La diferencia de valor
percibido entre uno y otro es enorme, y el trabajo extra es de un par de días.

---

## Qué hace el flujo

```
Día 20, 09:00
      │
      ▼
Descargar datos oficiales      (scripts/descargar_datos.py --forzar)
      │
      ▼
Procesar y reajustar curvas    (scripts/preparar_datos.py)
      │
      ▼
Detectar anomalías             (scripts/detectar_anomalias.py --json)
      │
      ▼
Armar el mensaje               (nodo Code, parsea el JSON)
      │
      ▼
¿Hay algo que reportar? ──── no ──▶ registrar y terminar (no molestar)
      │
     sí
      ▼
Telegram / mail / Slack
```

El workflow importable está en `automatizacion/n8n-monitor-mensual.json`.

---

## Por qué está diseñado así

### El principio: n8n orquesta, Python analiza

La tentación es hacer el análisis dentro de n8n con nodos. **No lo hagas.** El
ajuste de una curva no lineal a 3.000 pozos no es trabajo para un motor de
workflows: sería lento, imposible de testear y no lo podrías correr fuera de n8n.

La división correcta:

| Herramienta | De qué se ocupa |
|---|---|
| **Python** | Descargar, limpiar, ajustar, detectar. Es testeable y corre solo. |
| **n8n** | *Cuándo* correr, qué hacer si falla, a quién avisar, en qué formato. |

Esta separación es un argumento de arquitectura que podés defender en una
entrevista, y también es la razón por la que el mismo código sirve para el
dashboard, para el flujo automático y para un notebook exploratorio.

### La interfaz entre los dos: JSON por stdout

`detectar_anomalias.py --json` imprime **solo JSON** por salida estándar. n8n
lo captura en `stdout` y el nodo Code lo parsea. Es la interfaz más simple
posible entre un script y un orquestador, y funciona con cualquier herramienta
(n8n, cron, GitHub Actions, Airflow).

### El filtro de "no hay nada que reportar"

El nodo `¿Hay algo que reportar?` existe por una razón que aprendiste en tu
negocio, no en un libro: **una alerta que llega todos los meses deja de leerse.**
Si el sistema manda un mensaje aunque no haya nada, en tres meses nadie lo abre y
el monitoreo murió aunque siga corriendo.

---

## Cómo montarlo

1. **Importá el workflow** en tu n8n: *Workflows → Import from file →*
   `automatizacion/n8n-monitor-mensual.json`.

2. **Cambiá `/ruta/a/vaca-muerta-analytics`** por la ruta real en los tres nodos
   *Execute Command*.

3. **Usá el Python del entorno virtual**, no el del sistema: `.venv/bin/python`.
   Si ponés `python` a secas, n8n va a usar el intérprete del sistema, que no
   tiene pandas instalado, y el flujo va a fallar con un `ModuleNotFoundError`
   confuso. Es el error número uno al automatizar scripts de Python.

4. **Configurá la credencial de Telegram** (o cambiá ese nodo por Gmail o Slack:
   el resto del flujo no cambia).

5. **Probalo a mano** con *Execute Workflow* antes de dejarlo agendado.

### Si n8n corre en Docker

Es el caso más común y donde más gente se traba: el contenedor de n8n **no ve
tu filesystem ni tiene Python con pandas**. Dos salidas:

- **Montar el proyecto** como volumen e instalar las dependencias dentro del
  contenedor (rápido de armar, incómodo de mantener).
- **Exponer el script como un webhook**: un servicio chico (FastAPI) del lado de
  Python, y n8n le pega con un nodo HTTP Request. **Es la opción más limpia** y
  la que conviene si algún día querés vender esto como servicio: separa
  responsabilidades de verdad y te deja escalar el análisis sin tocar n8n.

---

## Extensiones naturales (en orden de valor)

| Extensión | Qué agrega |
|---|---|
| **Reporte mensual en PDF** | Nodo extra que genera el resumen del mes y lo manda por mail. Es lo que un gerente realmente quiere recibir. |
| **Alerta de dato nuevo publicado** | Chequear a diario el `metadata_modified` del dataset vía API, y disparar solo cuando cambió, en vez de agendar a ciegas. Más elegante y más robusto. |
| **Resumen escrito por IA** | Pasarle las anomalías a un modelo para que redacte el análisis en lenguaje natural. Encaja directo con tu marca. **Con una condición:** que el modelo redacte sobre números que ya calculaste, nunca que los calcule él. |
| **Histórico de detecciones** | Guardar cada corrida en una base para poder responder *"¿este pozo ya venía desviado?"*. Convierte alertas sueltas en una serie de tiempo. |

---

## Lo que esto vale para tu marca

El caso que le contás a un dueño de PyME no menciona petróleo:

> *"Tengo un sistema que todos los meses baja datos de un organismo público, los
> procesa con un modelo estadístico, detecta lo que se salió de lo esperado y
> manda un reporte. Nadie toca nada. La misma mecánica sirve para tus ventas,
> tu stock o tu cobranza."*

La mecánica es idéntica: **fuente de datos → procesamiento → detección de
desvíos → aviso**. Solo cambia qué es un "desvío".

Y tenés algo que la mayoría de quienes venden automatización no tiene: **un caso
público, verificable y técnicamente serio** que demuestra que el sistema
funciona. No es una demo armada para vender. Es un proyecto real con datos
reales, y cualquiera puede abrir el link y verlo.
