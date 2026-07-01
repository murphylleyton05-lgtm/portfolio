# 🟢 WhatsApp + CRM + IA — Stack de automatización self-hosted

Solución **self-hosted** que junta atención por WhatsApp, CRM y automatización con IA en un solo servidor. Pensada para PyMEs que quieren **pagar una vez** y no depender de suscripciones mensuales de software.

> Caso real: implementación para una tienda de tecnología importada (Xelvia Store).

## ¿Qué resuelve?

- 💬 **Atención por WhatsApp** con la API oficial de Meta (Coexistencia: el dueño sigue usando su celular normal)
- 🗂️ **CRM integrado**: contactos, etiquetas, notas y segmentos (dentro de Chatwoot, sin apps extra ni Trello)
- 🤖 **Respuestas automáticas con IA** (Claude): entiende la consulta, responde y clasifica al contacto
- 💵 **Pago único de software**: todo open source, solo se paga el VPS (~USD 7/mes)

## Stack

| Componente | Rol |
|-----------|-----|
| **Chatwoot** | Bandeja de entrada omnicanal + CRM |
| **n8n** | Orquestador de automatizaciones |
| **Claude (Anthropic)** | Motor de IA que entiende y redacta respuestas |
| **WhatsApp Cloud API** | Canal oficial (con Coexistencia) |
| **Docker Compose** | Todo el stack en un comando |

## Arquitectura

```
Cliente (WhatsApp)
      │
      ▼
WhatsApp Cloud API (Meta)
      │
      ▼
   Chatwoot  ──►  CRM (contactos + etiquetas)
      │  (webhook: message_created)
      ▼
    n8n  ──►  Claude (entiende + responde)
      │
      └──►  responde por WhatsApp + etiqueta el contacto
```

## Estructura

```
whatsapp-crm-automation/
├── docker-compose.yml       # Chatwoot + n8n + Postgres + Redis
├── .env.example             # Variables (copiar a .env)
├── n8n/
│   └── workflow-whatsapp-ia.json   # Automatización WhatsApp → IA → CRM
└── docs/
    └── INSTALL.md           # Guía de instalación paso a paso
```

## Instalación

Ver **[docs/INSTALL.md](./docs/INSTALL.md)** — guía completa para desplegar en un VPS (Hostinger) en 1-2 horas.

---

Implementado por **Lleyton Murphy** · Lleyton IA Automation
