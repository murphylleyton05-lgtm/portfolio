# 🎯 Cazador de Empleos Remotos PRO (n8n)

Automatización que **busca sola** empleos remotos que encajan con tu perfil y te manda solo los **nuevos** por email, dos veces por semana. Corre para siempre en tu propio n8n.

## Qué hace

```
[Cada martes y viernes 9hs]
        ↓
[4 búsquedas en la API de Remotive]  (Automation/IA · Data Analyst · Partnerships · Sales)
        ↓
[Une · deduplica · descarta ruido · deja solo los NUEVOS]   ← recuerda lo ya enviado
        ↓
[Rankea por fit (🔥 a los top) y arma un email maquetado]
        ↓
[Si hay nuevos → te lo envía por Gmail]
```

## Lo que trae de fábrica

- **4 fuentes de búsqueda** para cubrir todos tus rubros.
- **Solo roles nuevos:** guarda en memoria los que ya te avisó (no te repite nada).
- **Filtro anti-ruido:** descarta títulos que no encajan (clearance, VP, staff engineer, etc.).
- **Ranking por fit:** prioriza por palabras clave de tu perfil y le pone 🔥 a los mejores.
- **Email lindo:** HTML maquetado con link directo para aplicar a cada puesto.
- **Sin API key:** usa [Remotive API](https://remotive.com/api-documentation), pública y gratuita.

## Cómo importarlo en n8n

1. n8n → **Import from File** → `workflow-cazador-empleos.json`
2. En el nodo **Enviar por Gmail**, conectá tu credencial de Gmail (OAuth).
3. (Opcional) Cambiá el email destino o los términos de búsqueda (`search=` en cada nodo "Buscar").
4. **Activá** el flujo. Trabaja solo, para siempre.

## Personalizar

- **Más rubros:** duplicá un nodo "Buscar" y cambiá el `search=` (ej. `product manager`, `growth`).
- **Otra frecuencia:** editá el cron del Trigger (`0 9 * * 2,5` = martes y viernes 9hs).
- **Otro canal:** cambiá el nodo Gmail por Telegram, Slack o WhatsApp.

---

Hecho por **Lleyton Murphy** · Lleyton IA Automation
