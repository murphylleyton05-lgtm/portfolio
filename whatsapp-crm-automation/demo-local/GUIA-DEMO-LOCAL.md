# Demo local del sistema (gratis, en tu compu) — paso a paso

Objetivo: correr Chatwoot + n8n + IA en tu propia PC, **sin gastar un peso**, para
grabar un video de ventas mostrando la IA respondiendo sola y el CRM cargándose.

> Único requisito con costo mínimo: una API key de Claude (Anthropic). El uso de la
> demo son **centavos**. Todo lo demás es gratis.

---

## Paso 1 — Instalar Docker Desktop (gratis)

1. Descargá **Docker Desktop** para Windows: https://www.docker.com/products/docker-desktop/
2. Instalalo, reiniciá la PC si lo pide, y abrilo (que quede corriendo, ícono de la ballena).

## Paso 2 — Bajar el proyecto

Opción fácil sin comandos:
1. Entrá a https://github.com/murphylleyton05-lgtm/portfolio
2. Botón verde **Code → Download ZIP**, y descomprimilo.
3. Entrá a la carpeta `portfolio/whatsapp-crm-automation/demo-local`.

## Paso 3 — Configurar

1. Copiá el archivo `.env.local.example` y renombralo a `.env.local`.
2. Abrilo con el Bloc de notas y completá dos cosas:
   - `SECRET_KEY_BASE`: pegá cualquier texto largo (60+ caracteres al azar).
   - `ANTHROPIC_API_KEY`: tu clave de Claude (`sk-ant-...`).
3. Guardá.

## Paso 4 — Levantar todo

Abrí una terminal en esa carpeta (en el explorador, escribí `cmd` en la barra de
dirección y Enter). Pegá estos comandos, uno por uno:

```bash
docker compose -f docker-compose.local.yml run --rm rails bundle exec rails db:chatwoot_prepare
docker compose -f docker-compose.local.yml up -d
```

La primera vez tarda unos minutos (descarga las imágenes). Cuando termina, ya está todo corriendo.

## Paso 5 — Crear tu Chatwoot

1. Abrí el navegador en **http://localhost:3000**
2. Creá la cuenta de administrador (nombre, email, contraseña — es local, inventá lo que quieras).
3. Entrá. Ese es tu panel de atención + CRM.

## Paso 6 — Conectar n8n

1. Andá a tu perfil en Chatwoot (abajo a la izquierda) → **Access Token** → copialo.
2. Pegalo en `.env.local` en `CHATWOOT_API_TOKEN` y guardá.
3. Reiniciá n8n para que tome el token:
   ```bash
   docker compose -f docker-compose.local.yml up -d n8n
   ```
4. Abrí **http://localhost:5678**, creá el usuario local de n8n.
5. **Import from File** → subí el workflow `../n8n/workflow-whatsapp-ia.json`.
6. Activá el workflow (interruptor arriba a la derecha).

## Paso 7 — Enchufar el chat con la IA

1. En Chatwoot: **Configuración → Bandejas de entrada → Agregar → Sitio web**. Completá
   cualquier nombre (ej. "Xelvia Demo") y creala.
2. En **Configuración → Integraciones → Webhooks → Agregar**:
   - URL: `http://n8n:5678/webhook/chatwoot-mensaje`
   - Evento: **message_created**
3. Guardá.

## Paso 8 — La magia (grabá esto)

1. En la bandeja "Sitio web", Chatwoot te da un link/preview del chat. Abrilo.
2. Escribí como si fueras un cliente: *"Hola, tienen iPhone 15 en stock? Cuánto sale?"*
3. En unos segundos, la **IA responde sola** dentro de Chatwoot y el contacto queda
   etiquetado en el CRM.

Probá 3 o 4 mensajes distintos (precio, envío, un producto). Eso es tu demo.

## Paso 9 — Grabar el video

En Windows, apretá **Win + G** (Xbox Game Bar) → botón de grabar. O usá cualquier grabador.
Mostrá: llega el mensaje del cliente → la IA responde → el contacto en el CRM. 1 o 2 minutos alcanza.

## Paso 10 — Apagar

Cuando termines:

```bash
docker compose -f docker-compose.local.yml down
```

Los datos quedan guardados para la próxima. Si querés borrar todo: agregá `-v` al final.

---

## Si algo falla

- **No abre localhost:3000** → esperá 1-2 min más (Chatwoot tarda en arrancar). Revisá con `docker compose -f docker-compose.local.yml ps` que todo esté "Up".
- **La IA no responde** → revisá que `ANTHROPIC_API_KEY` esté bien y que el workflow esté **activo** en n8n.
- **Chatwoot no llama a n8n** → verificá que la URL del webhook sea exactamente `http://n8n:5678/webhook/chatwoot-mensaje`.

Cualquier error, me lo pegás y lo resolvemos.
