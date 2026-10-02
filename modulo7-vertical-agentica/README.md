# 🧭 Checkpoint 7 · Diseño Arquitectónico de un Sistema Agéntico Vertical de Industria

**Entregable:** 📄 [`PreEntrega_Modulo7_LleytonMurphy.pdf`](./PreEntrega_Modulo7_LleytonMurphy.pdf). Informe de consultoría de 10 páginas, organizado en las 4 “páginas” de la consigna más un anexo con el checklist. La fuente editable es [`informe_m7_fuente.html`](./informe_m7_fuente.html).

**Vertical:** Customer Success & Sales Ops (postventa y retención) del e-commerce del proyecto integrador (Lleyton Tech Store, M1 → M6). Enfoque 100% no-code con n8n y conectores nativos.

| Página | Contenido |
|---|---|
| **1 · Relevamiento** | Problema operativo, justificación agéntica, baseline manual (≈ 454 h/mes, primera respuesta en 9 h, 62% de renovación, ≈ $2,73 M/mes en riesgo) y framework de priorización (impacto, viabilidad no-code, adopción y accesos regulados) |
| **2 · Arquitectura** | Canvas de coreografía (orquestador + 4 especialistas), ficha de cada agente con System Prompt y contrato JSON, Context Engineering por sub-workflow y mapa de permisos de mínimo privilegio |
| **3 · Valor y riesgo** | Propuesta de valor comercial, 9 KPIs con baseline y meta, semáforo verde/amarillo/rojo y protocolo de escalado con botones Aprobar/Rechazar en Slack |
| **4 · Scorecards** | Health Score de renovación, rúbrica de reembolsos por tags normalizados con evidencia, Playbook de objeciones y versión de portafolio anonimizada |

**Agentes:** Orquestador de Postventa · ① Resolutor de Política (RAG del M5) · ② Gestor de Reembolsos · ③ Guardián de Retención y Objeciones · ④ Auditor de Atribución de Ingresos.

---

Hecho por **Lleyton Murphy** · Lleyton IA Automation
