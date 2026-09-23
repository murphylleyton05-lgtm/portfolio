# 🔌 Checkpoint 4 · Integraciones Avanzadas e Interconexión de Sistemas (n8n)

**Entregable:** ⚙️ [`checkpoint4_lleyton_murphy.json`](./checkpoint4_lleyton_murphy.json): flujo de n8n (*Workflow → Import from File*). Hay una copia en la raíz del repo: [`/checkpoint4_lleyton_murphy.json`](../checkpoint4_lleyton_murphy.json).

Es el mismo proyecto integrador del [M3](../modulo3-memoria), con la memoria por cliente en la Data Table `Memoria Agente M3`. Ahora está conectado a **3 herramientas reales del e-commerce vía OAuth2**:

| Rol en el caso del vivo | Herramienta | Lectura (pasado) | Escritura (futuro) |
|---|---|---|---|
| CRM / fuente única de verdad | **HubSpot** | `Search` contacto por email | `Create or Update` del contacto (solo email, nombre, lifecycle, message) |
| Casilla de soporte | **Gmail** | `Gmail Trigger` (no leídos del inbox) | **solo** `Create Draft` (nunca envía) |
| Canal del equipo | **Slack** | — | `Post message` en `#ops-soporte` |

## Circuito

```
[Gmail Trigger · casilla soporte]
        │
①  [IF Anti Auto-Reply] ── Sí ─▶ [Stop: auto-reply ignorado]   (corta el bucle infinito)
        │ No
[Leer Memoria Cliente (M3)] → [AI Agent · clasifica y redacta (GPT-4o-mini + parser JSON)]
        │
④  [Set Limpieza Payload]  (From, Subject, BodyText + categoría/prioridad/resumen/borrador; sin HTML, headers ni binarios)
        │
   [IF Email válido] ── No ─▶ [Descartar]   (evita el 400)
        │ Sí
②  [Look up contacto en HubSpot]
   ┌────┴─────┐
   Sí          No
[Update]    [Create contacto]              (evita el 409)
   └────┬─────┘
③  [Create Draft en Gmail]                (Human-in-the-loop: un humano revisa y envía)
        │
   [Set Payload Mínimo Slack] → [Slack #ops-soporte] → [Actualizar Memoria Cliente (M3)]
```

## Cumplimiento de la consigna

| Paso | Implementación |
|---|---|
| 1. Tres conectores nativos | `Gmail Trigger` + `Gmail`, `HubSpot` v2.2, `Slack` v2.3. |
| 2. OAuth2 | Los nodos usan `authentication: oAuth2` (Gmail OAuth2, HubSpot OAuth2, Slack OAuth2). Las credenciales **no van en el JSON**: al importarlo, se elige o crea la credencial en cada nodo con *Sign in with…* hasta ver el semáforo en verde. |
| 3. Mínimo privilegio | Gmail: `gmail.readonly` + `gmail.compose` (sin `gmail.send`). HubSpot: `crm.objects.contacts.read` + `crm.objects.contacts.write`, y el Search trae solo `email, firstname, lastname`. Slack: `chat:write` en un único canal. Adjuntos desactivados (`downloadAttachments: false`). |
| 4–5. IF anti auto-reply | Primer nodo después del trigger. Condición **OR**, sin distinguir mayúsculas: asunto con `Auto-reply`, `Automatic reply`, `Out of office`, `Undeliverable`, `Delivery Status Notification`, `Respuesta automática`, `Fuera de la oficina`; remitente con `no-reply@`, `noreply@`, `mailer-daemon`; o header `Auto-Submitted: auto-*`. La rama verdadera termina en un Stop. |
| 6. Look up antes del Create | `HubSpot → Contact → Search` por `email = From` (con *Always Output Data*) → `IF ¿Contacto existe?` → Update o Create. Así nunca se intenta crear un duplicado (409). |
| 7. Create Draft (HITL) | `Gmail → Draft → Create` con `sendTo` y `threadId` del correo original. El workflow no tiene ninguna operación *Send*. |
| 8. Set antes de mensajería | `④ Set Limpieza Payload` (con *Include Other Fields* en off y *Strip Binary*) recorta el cuerpo a 2000 caracteres. `Set Payload Mínimo Slack` deja 8 campos cortos para el canal. |
| 9. Test de regresión | Ver abajo. |

## Cómo importarlo y probarlo

1. En n8n: **Workflows → Import from File** → `checkpoint4_lleyton_murphy.json`.
2. Abrir cada nodo de Gmail, HubSpot y Slack y conectar su credencial OAuth2 (*Sign in with Google / HubSpot / Slack*).
3. En `Slack Canal Operaciones`, elegir el canal del equipo. Por defecto es `#ops-soporte`.
4. Si no tenés la Data Table del M3, creá `Memoria Agente M3` con las columnas `session_id, user_name, fecha_actualizacion, resumen_consolidado, estado_del_caso, message_count` y seleccionala en los dos nodos de memoria.
5. Test de regresión con **Test step** nodo por nodo, o con **Execute Workflow**:
   - Mandar a la casilla un mail con asunto `Out of office` → debe terminar en *Stop: Auto-Reply Ignorado*.
   - Mandar un mail normal desde un remitente nuevo → *Create Contacto* + borrador en Gmail + aviso en Slack.
   - Repetir desde el mismo remitente → ahora pasa por *Update Contacto* (sin duplicado) y la memoria incrementa `message_count`.

---

Hecho por **Lleyton Murphy** · Lleyton IA Automation
