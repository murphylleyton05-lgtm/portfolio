# ✅ Checkpoint 1 · Agente Autónomo Básico Funcional (n8n)

**Entregable:** [`checkpoint1_lleyton_murphy.json`](./checkpoint1_lleyton_murphy.json) — flujo exportado de n8n, listo para *Import from File*.

Agente de razonamiento base (Módulo 1) del proyecto integrador. Construido y **probado de punta a punta** en n8n Cloud (ejecución exitosa, el agente abre la herramienta de forma autónoma y escribe el log).

## Arquitectura

```
[Chat Trigger] → [AI Agent · Tools Agent] → [Log de Observabilidad] → [Respuesta al usuario]
                     │            │
        [OpenAI Chat Model]   [buscar_vacantes_remotas]  (herramienta lateral)
```

## Cumplimiento de la consigna

| Requisito | Implementación |
|---|---|
| **Trigger** | `Chat Trigger` — captura el mensaje desestructurado del usuario. |
| **AI Agent en modo Tools Agent** | Nodo `AI Agent` (v3.1, que en n8n es Tools Agent por defecto). |
| **Chat Model estratégico** | `OpenAI Chat Model` → **GPT-4o** (vía créditos Gateway de n8n). |
| **Guardrail de iteraciones** | `maxIterations = 6` (dentro del rango 5–10). |
| **System Prompt modular** | Rol → Ámbito → Objetivo → Reglas/Restricciones → Escalamiento, con límites explícitos de lo que **NO** debe hacer. |
| **Herramienta lateral funcional** | `buscar_vacantes_remotas` (HTTP Request Tool → API pública de Remotive) conectada como **extensión (`ai_tool`)**, no como nodo secuencial. Con **descripción semántica extensa** de cuándo activarla. |
| **Observabilidad** | Nodo `Log de Observabilidad` (Data Table de n8n) que registra fecha, session_id, mensaje del usuario, respuesta del agente y herramienta disponible. |

## Prueba realizada (en verde)

Prompt de prueba: *"Buscá vacantes remotas de data analyst para aplicar"* →
el agente **decidió invocar la herramienta** (`tool_calls.completed: 1`), trajo vacantes reales
de Remotive, devolvió la lista y escribió la fila en el log. Ejecución **success**.

## Notas

- El **modelo usa los créditos Gateway** de n8n: no requiere API key propia.
- El **log usa una Data Table nativa** (persistencia sin credenciales). Es intercambiable por
  un nodo final de **Gmail / Slack** conectando una credencial OAuth, sin cambiar el resto del flujo.
- Para importarlo: n8n → *Import from File* → `checkpoint1_lleyton_murphy.json`. El modelo toma la
  credencial Gateway automáticamente; la herramienta HTTP no necesita credenciales.

---

Hecho por **Lleyton Murphy** · Lleyton IA Automation
