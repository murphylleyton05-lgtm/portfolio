# 🤖 Checkpoint 1 — Agente Base (Tools Agent) en n8n

Primera versión del **proyecto integrador**: un agente autónomo básico funcional construido en n8n.
Actúa como **Asistente de Calificación de Leads B2B** y es la base que se irá ampliando módulo a
módulo (memoria, integraciones reales, RAG, voz, etc.).

## 📦 Entregable

- `checkpoint1_lleyton_murphy.json` — flujo exportado de n8n, listo para importar.

## 🗺️ Arquitectura del flujo

```
[Chat Trigger] → [AI Agent · Tools Agent] → [Observabilidad · Gmail]
                        │
      ┌─────────────────┼─────────────────┐
      │                                   │
[Anthropic Chat Model]        [Google Sheets Tool]
 (Claude 3.5 Sonnet)          (Registrar Lead)
```

## ✅ Componentes obligatorios (cómo se cumplen)

| Requisito | Implementación |
|-----------|----------------|
| **Disparador** | Nodo `Chat Trigger` que captura el mensaje desestructurado del usuario. |
| **AI Agent (cerebro)** | Nodo `AI Agent` en modo **Tools Agent**. |
| **Modelo de lenguaje** | `Anthropic Chat Model` conectado por su puerto nativo (`ai_languageModel`), usando **Claude 3.5 Sonnet**. |
| **Guardrail de iteraciones** | `Max Iterations = 8` (rango exigido 5–10) para blindar el presupuesto contra bucles infinitos. |
| **System Prompt modular** | Estructura **Rol → Ámbito → Objetivo → Reglas → Escalamiento**, con límites estrictos de alcance y **exclusión explícita del lenguaje inclusivo**. |
| **Herramienta (Tool)** | `Google Sheets Tool` acoplado **lateralmente** al agente (`ai_tool`), nunca como nodo secuencial. Incluye una **descripción semántica extensa** que le indica al modelo en qué casos de negocio activarla de forma autónoma. |
| **Observabilidad** | Nodo final `Gmail` que envía un reporte con la entrada del usuario y la salida del agente (Execution Log) para supervisión humana. |

## 🔧 Cómo usarlo

1. En n8n: **Workflows → Import from File** y seleccioná `checkpoint1_lleyton_murphy.json`.
2. Reemplazá las credenciales marcadas como `REEMPLAZAR_*`:
   - **Anthropic API** (para el Chat Model).
   - **Google Sheets OAuth2** (para la herramienta de registro de leads).
   - **Gmail OAuth2** (para el reporte de observabilidad).
3. En el nodo de Google Sheets, reemplazá `REEMPLAZAR_ID_GOOGLE_SHEET` por el ID de tu planilla
   (hoja `Leads` con las columnas: Fecha, Nombre, Empresa, Rubro, Necesidad, Presupuesto, Puntaje,
   Clasificacion, Etiqueta).
4. **Execute Workflow** y enviá un prompt de prueba, por ejemplo:
   > *"Hola, soy Juan Pérez de Aceros del Sur. Necesitamos automatizar el seguimiento de
   > cotizaciones, tenemos presupuesto y queremos arrancar este mes."*
5. Auditá el panel de ejecución en verde: el agente debe abrir la ramificación de la herramienta,
   registrar el lead y enviar el reporte de observabilidad.

## 🧠 Diseño agéntico

- **Automatización lineal determinista:** el nodo final de observabilidad (Gmail) siempre se ejecuta.
- **Autonomía probabilística (ciclo ReAct):** el agente decide por sí mismo si activa la herramienta
  de Google Sheets según la temperatura del lead, evitando la "instrucción huérfana".
