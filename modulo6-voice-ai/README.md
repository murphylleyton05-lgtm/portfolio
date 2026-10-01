# 🎙️ Checkpoint 6 · Ecosistemas Multimedia de Audio (Voice AI) en n8n

**Entregables:**
- 📄 [`PreEntrega_Modulo6_LleytonMurphy.pdf`](./PreEntrega_Modulo6_LleytonMurphy.pdf): capturas de la configuración visual en n8n, diagnóstico de viabilidad (ROI y fatiga cognitiva) y extracto del flujo en formato texto.
- ⚙️ [`checkpoint6_lleyton_murphy.json`](./checkpoint6_lleyton_murphy.json): flujo exportado de n8n (*Import from File*).

Parte del workflow del [Módulo 5](../modulo5-rag) (Gmail + HubSpot + Slack + RAG) y le suma un **carril de voz por Telegram** que consulta la misma base documental (`politicas_tienda_v2_1`).

## Circuito cerrado

```
[Telegram Trigger] → [Get File · binario data] → [OpenAI Whisper · data · es]
        → [IF ¿Transcripción válida?]
              ├─ true  → [AI Agent Voz (Tools Agent) + consultar_manual_politicas (RAG M5)]
              │           → [Tope 200 caracteres] → [ElevenLabs · Multilingual v2] → [Telegram Send Audio]
              └─ false → [Telegram · Aviso audio inválido (texto)]
        → [🔒 Purga binaria (Compliance)]
```

| Requisito | Implementación |
|---|---|
| Interceptación binaria | Telegram Trigger (bot oficial, webhook) + Get File → binario `data`. El trigger de n8n no descarga notas de voz (solo foto, video y documento), por eso se usa Get File. |
| Whisper | Input Binary Property `data`, idioma `es`, temperatura 0, *On Error: Continue*. |
| Cerebro | AI Agent v3 (Tools Agent) con gpt-4o-mini y la tool RAG del M5. |
| Contención financiera | System Message ≤ 200 caracteres + Max Tokens 120 + guardrail que corta en la última oración completa. |
| Voz | ElevenLabs Multilingual v2, voz Sarah, Stability 0.60, Clarity (similarity_boost) 0.80, MP3 64 kbps. |
| Salida | Telegram **Send Audio** con el binario `data` de ElevenLabs, caption con el texto y respuesta citando la nota original. |
| Contingencia | IF: sin error, ≥ 3 caracteres y sin alucinaciones de Whisper (“[Ruido…]”, “(Música…)”, frases en bucle, “Amara.org”). Si falla, avisa por texto. |
| Compliance | No se guarda ninguna ejecución + purga final sin binarios ni transcripción + agente sin memoria. En la instancia: `N8N_DEFAULT_BINARY_DATA_MODE=default`, `EXECUTIONS_DATA_HARD_DELETE_BUFFER=0`, `EXECUTIONS_DATA_PRUNE_HARD_DELETE_INTERVAL=1` (audio solo en RAM y purga en menos de 1 min, medido). |

## Prueba de punta a punta

El carril de voz se ejecutó en n8n 2.41.5 con una nota de voz real y Whisper real (open source, local). Telegram, el LLM y ElevenLabs se reemplazaron por simuladores que registran lo que n8n envía. Detalle, registro y audios en [`prueba-e2e/`](./prueba-e2e) y en la sección 11 del PDF.

## Puesta en marcha

1. Importar el `.json` en n8n.
2. Asignar las credenciales Telegram API, OpenAI y ElevenLabs. El nodo de ElevenLabs es el paquete verificado `@elevenlabs/n8n-nodes-elevenlabs`.
3. Ejecutar una vez “Cargar Manual (ejecutar 1 vez)” para indexar el manual del M5.
4. (Self-hosted) Definir las 3 variables de Compliance y reiniciar n8n.
5. Publicar el workflow (un solo webhook por bot de Telegram).

---

Hecho por **Lleyton Murphy** · Lleyton IA Automation
