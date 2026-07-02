# 🎯 Cazador de Empleos Remotos (n8n)

Automatización que **busca sola** empleos remotos que encajan con tu perfil y te los manda por email, dos veces por semana. Corre para siempre en tu propio n8n.

## Qué hace

```
[Cada martes y viernes 9hs]
        ↓
[Busca en la API de Remotive] × 2 (Automation/IA + Data Analyst)
        ↓
[Une, deduplica y rankea por fit]
        ↓
[Arma un email con los 10 mejores + links para aplicar]
        ↓
[Te lo envía por Gmail]
```

- **Fuente de datos:** [Remotive API](https://remotive.com/api-documentation) — pública y gratuita, sin API key.
- **Salida:** email a tu casilla con los roles y el link directo para aplicar.
- **Ranking:** prioriza títulos con palabras clave de tu perfil (automation, AI, partnerships, sales, data, analyst, no-code...).

## Cómo importarlo en n8n

1. n8n → **Import from File** → `workflow-cazador-empleos.json`
2. En el nodo **Enviar por Gmail**, conectá tu credencial de Gmail (OAuth).
3. (Opcional) Cambiá el email destino y los términos de búsqueda de los nodos "Buscar".
4. **Activá** el flujo. Listo — trabaja solo.

## Personalizar

- **Más rubros:** duplicá un nodo "Buscar" y cambiá el `search=` de la URL (ej. `search=sales`, `search=partnerships`).
- **Otra frecuencia:** editá el cron del Trigger (`0 9 * * 2,5` = martes y viernes 9hs).
- **Otro canal:** cambiá el nodo Gmail por Telegram, Slack o WhatsApp.

---

Hecho por **Lleyton Murphy** · Lleyton IA Automation
