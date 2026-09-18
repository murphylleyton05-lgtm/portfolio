# 🧠 Checkpoint 3 · Memoria Persistente y Resumen Automático (n8n)

**Entregables:**
- 📄 [`PreEntrega_Modulo3_Lleyton_Murphy.pdf`](./PreEntrega_Modulo3_Lleyton_Murphy.pdf) — documento técnico (3 páginas: lienzo, prompt de summarization, esquema de datos).
- ⚙️ [`checkpoint3_memoria_lleyton_murphy.json`](./checkpoint3_memoria_lleyton_murphy.json) — flujo exportado de n8n (*Import from File*).

Capa de **memoria de largo plazo** por `Session_ID` sobre la arquitectura del Módulo 2. Construida y **probada de punta a punta** en n8n Cloud.

## Circuito

```
[Chat Trigger] → [Leer Memoria por Session_ID] → [IF ¿existe?]
      ├─ NO  → [Crear Registro Inicial] → [Set Contexto Nuevo] ┐
      └─ SÍ  → [Set Contexto Recurrente] ───────────────────────┤→ [Contexto listo]
                                                                 → [AI Agent · Tools Agent + memoria inyectada]
                                                                 → [IF ¿message_count > 5?]
      ├─ SÍ → [Summarization JSON (GPT-4o-mini + parser)] → [Preparar Resumen] → [Actualizar Memoria (idempotente)]
      └─ NO → [Actualizar Contador]
                                                                 → [Respuesta al usuario]
```

## Cumplimiento de la consigna

| Requisito | Implementación |
|---|---|
| **Persistencia por Session_ID** | Data Table `Memoria Agente M3`; lectura con *get* filtrando `session_id`. |
| **IF usuario nuevo vs recurrente** | Rama nueva crea registro limpio (sin variables vacías); rama recurrente recupera contexto. |
| **Inyección de contexto** | En el System Prompt del Tools Agent, con delimitadores rígidos `[INICIO DE CONTEXTO COMPARTIDO] … [FIN DEL CONTEXTO COMPARTIDO]` (anti prompt-injection). |
| **Summarization > 5 mensajes** | `IF message_count > 5` → LLM económico (GPT-4o-mini) + Structured Output Parser → JSON `{asunto_principal, puntos_clave[], accion_requerida}`. |
| **Escritura idempotente** | *Update* del registro por `session_id`, sobrescribiendo el resumen anterior. |
| **Sin ruido en la base** | Solo se persiste el resumen analítico + indicadores; nunca HTML, logs ni transcripciones completas. |

## Esquema de la base (Data Table `Memoria Agente M3`)

| Columna | Tipo | Rol |
|---|---|---|
| `session_id` | string | Clave de aislamiento por sesión |
| `user_name` | string | Nombre del usuario |
| `fecha_actualizacion` | string (ISO) | Timestamp de última escritura |
| `resumen_consolidado` | string (JSON) | `{asunto_principal, puntos_clave, accion_requerida}` |
| `estado_del_caso` | string | Estado / próxima acción |
| `datos_clave` | string (JSON) | Array de hechos clave |
| `message_count` | number | Contador de intercambios (dispara summarization > 5) |

## Prueba realizada (en verde)

- **Usuario nuevo:** crea el registro, el agente saluda por nombre y trae vacantes reales; actualiza contador. ✅
- **Summarization:** al superar el umbral, el modelo mini devolvió un JSON estructurado válido y se persistió idempotente en `resumen_consolidado`. ✅

## Notas

- Base de memoria en **Data Table nativa de n8n** (sin credenciales), **equivalente 1:1 a Airtable** en columnas y tipos. Para usar Airtable real: reemplazar los nodos Data Table por nodos Airtable (Search / Create / Update) con las mismas columnas y una credencial de Airtable.
- Modelos vía **créditos Gateway** de n8n (sin API key propia).

---

Hecho por **Lleyton Murphy** · Lleyton IA Automation
