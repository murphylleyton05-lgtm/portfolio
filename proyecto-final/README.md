# Proyecto Final · Sistema agéntico de soporte supervisado

**AI Experto · Cohorte 2026 · Lleyton Murphy**

Sistema Manager-Worker en n8n para la atención al cliente de Lleyton Tech Store. Cada consulta llega por webhook y recibe un acuse en milisegundos. La respuesta se genera solo con el Manual de Políticas v2.1 (RAG con citas verificables) y la audita un Supervisor de Calidad (AI-as-a-Judge) antes de tocar el CRM o llegar al cliente. Lo riesgoso o dudoso pasa a una cola de aprobación humana.

📄 **Documento Maestro (DMSA):** [`Murphy_Lleyton_ProyectoFinal_AI_Experto.pdf`](./Murphy_Lleyton_ProyectoFinal_AI_Experto.pdf)

## Resultados medidos

| Métrica | Valor |
|---|---|
| Acuse al cliente (202 + trace_id) | 283 ms |
| Acuerdo del Juez (gpt-4o) con la revisión humana | 11/11 · exactitud media 4,82/5 |
| Respuesta defectuosa inyectada | RECHAZADO 1/5 → cola humana |
| Costo de IA por consulta | USD 0,0037 (USD 3,68 cada 1.000) |
| Tokens por mes (1.500 consultas) vs horas liberadas | USD 5,52 vs USD 1.560 |

## Workflows (`workflows/`)

| Archivo | Rol |
|---|---|
| `PF1_Manager.json` | Webhook `POST /pf-soporte`, idempotencia, 202 inmediato, memoria + semáforo, ruteo por veredicto |
| `PF2_Worker_RAG.json` | Resolutor de políticas: Top-K 4, score ≥ 0,40, citas con metadatos reales, regla «No sé», autorreparación del índice |
| `PF3_Supervisor_QA.json` | Juez gpt-4o con JSON Schema estricto, umbral exactitud ≥ 4, fail-safe |
| `PF4_CRM_Despacho.json` | CRM + Gmail al cliente, idempotente por trace_id, salida de error |
| `PF5_Cola_HITL.json` | Cola de aprobación humana con token de un solo uso y aviso por Gmail |
| `PF6_Decision_humana.json` | Webhook `GET /pf-decision` (Aprobar / Rechazar) |
| `PF7_Alertas_error.json` | Error Trigger compartido: PF Incidentes + Gmail al equipo |
| `PF8_Banco_pruebas.json` | Banco de regresión: 11 casos y A/B del modelo Juez |

## Cómo importarlo

1. Importar los 8 JSON en n8n. **Primero PF 2 a PF 7**, para que existan los sub-workflows, y después PF 1 y PF 8. Volver a seleccionar en cada nodo «Ejecutar PF …» el sub-workflow correspondiente (los IDs cambian al importar).
2. Crear las Data Tables del Anexo A.4 del DMSA (PF Solicitudes, Memoria Agente M3, PF Base Conocimiento, PF Auditoria Trazas, PF Cola Aprobacion, PF CRM Casos, PF Incidentes) y cargar en PF Base Conocimiento las 15 secciones del Manual v2.1.
3. Crear las credenciales (los JSON no traen ninguna):
   - `openAiApi`: Resolutor, embeddings y Juez.
   - `gmailOAuth2`: PF 4, PF 5 y PF 7.
4. Completar los parámetros marcados con `<__PLACEHOLDER_VALUE__…>`:
   - `email_supervisor` en PF 1 y PF 7.
   - `url_decision` con la URL de la propia instancia.
5. Publicar PF 7, configurarlo como *Error workflow* de PF 1 a PF 6 y publicar PF 1 y PF 6.

## Prueba rápida

```bash
curl -X POST https://<instancia>.app.n8n.cloud/webhook/pf-soporte \
  -H 'Content-Type: application/json' -H 'Idempotency-Key: prueba-001' \
  -d '{"email":"cliente@ejemplo.com","nombre":"Ana","mensaje":"¿Cuánto tarda un envío a Mendoza?"}'
# → 202 {"estado":"recibido","trace_id":"trc-…","procesamiento":"asincrono"}
```

El mismo `curl` con la misma `Idempotency-Key` responde `200 "duplicada"` y no reprocesa ni reenvía.

## Evidencia (`evidencia/`)

- `lienzo/pf1.png` … `pf8.png`: capturas del lienzo de cada workflow.
- `bateria_regresion_exec47.json`: salida completa del banco de regresión. Incluye los 22 veredictos con sus JSON, los tokens y el costo por caso.

## Seguridad

No hay API keys, tokens OAuth ni contraseñas en este repositorio. Las credenciales se guardan cifradas en n8n y los workflows no las incluyen.
