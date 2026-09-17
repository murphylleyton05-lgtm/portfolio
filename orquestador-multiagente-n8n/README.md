# 🧠 Orquestación Multi-Agente con Sub-workflows (n8n) — Módulo 2

Refactor del agente base del **Módulo 1** ("Cazador de Empleos") hacia una arquitectura
**Manager–Worker** de grado empresarial, con sub-workflows independientes, contrato de datos
JSON y log de trazabilidad.

> Proyecto integrador — se sigue ampliando hasta el Proyecto Final (M11). Guardá los `.json`.

## 🗺️ Arquitectura

```
                         ┌──────────────────────────────────────────────┐
                         │              MANAGER (Orquestador)            │
                         │                                               │
  ▶ Trigger ─► Set consulta ─► 🤖 Router de Triaje (IA) ─► Parser (+fallback) ─► Switch
                         │                                                    │  (taxonomía cerrada)
                         │        ┌───────────── BUSQUEDA_EMPLEOS ───────────┤
                         │        │              REDACCION_EMAIL ────────────┤
                         │        │              ESCALAR_HUMANO (fallback) ──┘
                         │        ▼
                         │   🧹 Set limpieza (payload mínimo viable)
                         │        ▼
                         │   Execute Workflow  ──(Wait for child = ON)──►  WORKER
                         │        ▼
                         │   Registro auditoría ─► 🗒️ Log Trazabilidad (Google Sheets)
                         └──────────────────────────────────────────────┘

   WORKER 1  (Execute Workflow Trigger) ─► Preparar búsquedas ─► HTTP Remotive ─► Consolidar+Rankear ─► CONTRATO JSON
   WORKER 2  (Execute Workflow Trigger) ─► Redactar correo ─────────────────────────────────────────► CONTRATO JSON
```

## 📦 Archivos

| Archivo | Rol |
|---|---|
| `manager_modulo2_murphy_lleyton.json` | Orquestador principal (trigger, router IA, switch, execute workflow, log) |
| `worker1_extraccion_datos_murphy_lleyton.json` | Especialista: extracción y análisis de vacantes (Remotive API) |
| `worker2_redaccion_email_murphy_lleyton.json` | Especialista: redacción de correos de postulación |

## 🚀 Cómo importarlo y correrlo

1. **Importá los 3 flujos**: n8n → *Import from File* → uno por uno los `.json`. **Guardá cada uno.**
2. **Enlazá los workers en el Manager**:
   - Nodo **Execute Workflow: Worker 1** → campo `workflowId` → seleccioná *"Worker 1 — Extracción..."*.
   - Nodo **Execute Workflow: Worker 2** → campo `workflowId` → seleccioná *"Worker 2 — Redacción..."*.
   - Verificá que **Wait for child to finish** esté **activado** (ya viene en `true`).
3. **Router de Triaje (IA)** — opcional pero recomendado:
   - Conectá una credencial en el nodo **OpenAI Chat Model** (o cualquier chat model).
   - **Modo sin tokens**: si no conectás credencial, el nodo continúa por error y el **Parser** clasifica
     con reglas deterministas por palabras clave. El flujo corre igual. ✅
4. **Log de Trazabilidad**: en el nodo **Google Sheets** conectá tu credencial y elegí el documento y la hoja.
   - Creá una hoja con columnas: `fecha | requestId | worker_invocado | parametros_enviados | status | respuesta`.
   - *(Alternativa: reemplazalo por un nodo Gmail o Slack.)*
5. **Probalo**: abrí el Manager → botón **Test workflow** (Ejecutar). Cambiá el texto en
   **Consulta del usuario** para forzar cada ruta:
   - `"Buscá vacantes de data analyst"` → **BUSQUEDA_EMPLEOS** (Worker 1)
   - `"Redactá un correo de postulación"` → **REDACCION_EMAIL** (Worker 2)
   - `"asdkjfh"` (ambiguo) → **ESCALAR_HUMANO** (fallback)

## 🔌 Contrato de datos (Interfaz Manager ⇄ Worker)

**Manager → Worker 1** (mínimo viable, sin data stuffing):
```json
{ "requestId": "REQ-1699...", "intencion": "BUSQUEDA_EMPLEOS", "terminos": ["automation","data analyst"], "limite": 12 }
```
**Manager → Worker 2**:
```json
{ "requestId": "REQ-1699...", "intencion": "REDACCION_EMAIL", "destinatario": "tu@mail.com", "tono": "profesional", "vacantes": [{"titulo":"...","empresa":"...","url":"..."}] }
```
**Worker → Manager** (contrato de salida estándar, éxito o contingencia):
```json
{ "status": "success", "worker": "worker1_extraccion_datos", "requestId": "REQ-...", "data": { "...": "..." }, "error": null }
```
```json
{ "status": "error", "worker": "worker1_extraccion_datos", "requestId": "REQ-...", "data": null, "error": { "code": "API_UNREACHABLE", "message": "..." } }
```

## 🧭 Criterio de enrutamiento (taxonomía cerrada)

| Categoría | Se delega a | Disparador |
|---|---|---|
| `BUSQUEDA_EMPLEOS` | Worker 1 (datos) | buscar/listar vacantes, puestos, oportunidades |
| `REDACCION_EMAIL` | Worker 2 (correos) | redactar/escribir correo, postulación, carta |
| `ESCALAR_HUMANO` | *fallback* → supervisor | intención dudosa, ambigua o fuera de taxonomía |

El **Router de Triaje (IA)** interpreta lenguaje natural y devuelve la categoría; el **Parser**
la normaliza y aplica un **fallback determinista** (0 tokens) si la IA no está disponible o responde
fuera de formato. El **Switch** enruta de forma determinista sobre `intencion`.

## 🛡️ Antipatrones evitados

- **Mono-Bloque** → cada especialista vive en su propio lienzo (`Execute Workflow Trigger`).
- **Pasillo de la Muerte / Data stuffing** → nodos **Set de limpieza** envían sólo el mínimo viable.
- **Time-outs** → HTTP con `timeout` y workers con `executionTimeout`; Manager pausa con *Wait for child*.
- **Fallos del Worker** → cada worker devuelve un **JSON de contingencia** (`status:"error"`) en vez de morir.

## 📸 Capturas para el PDF (`preentrega_modulo2_murphy_lleyton.pdf`)

1. Lienzo del **Manager completo** con el nodo *Execute Workflow* visible.
2. Lienzo del **Worker 1** (con *Execute Workflow Trigger* + nodo de salida/contrato).
3. Lienzo del **Worker 2** (ídem).
4. Config del nodo **Execute Workflow** mostrando el paso de datos y **Wait for child to finish** = ON.
5. **Panel de ejecución** con una corrida exitosa de punta a punta (Manager → Worker → retorno).
6. La fila registrada en el **Log de Trazabilidad**.

---

Hecho por **Lleyton Murphy** · Lleyton IA Automation
