# Guía de instalación — Chatwoot + n8n + WhatsApp (Coexistencia)

Guía para dejar andando el stack en un VPS de Hostinger (o cualquier VPS Ubuntu 22.04+).
Tiempo estimado: 1-2 horas.

## 0. Requisitos

- 1 VPS con **Ubuntu 22.04+**, mínimo **2 vCPU / 2-4 GB RAM** (Hostinger KVM 2 va bien).
- 1 **dominio** (o dos subdominios): `chat.tudominio.com` (Chatwoot) y `n8n.tudominio.com` (n8n).
- Cuenta de **Meta Business** con un número de WhatsApp habilitado.
- Una **API key de Anthropic** (Claude) para la IA.

## 1. Preparar el servidor

```bash
# Conectarse por SSH
ssh root@IP_DEL_VPS

# Instalar Docker + Docker Compose
curl -fsSL https://get.docker.com | sh
apt-get update && apt-get install -y git
```

## 2. Bajar este proyecto

```bash
git clone https://github.com/murphylleyton05-lgtm/portfolio.git
cd portfolio/whatsapp-crm-automation
cp .env.example .env
```

## 3. Completar el `.env`

Generá los secretos:

```bash
openssl rand -hex 64   # -> SECRET_KEY_BASE
openssl rand -hex 24   # -> N8N_ENCRYPTION_KEY
```

Editá `.env` y completá: dominios (`FRONTEND_URL`, `N8N_HOST`), contraseñas de Postgres/Redis/n8n y los secretos generados. **Importante:** la `REDIS_PASSWORD` debe ser la misma en `REDIS_PASSWORD` y dentro de `REDIS_URL`.

## 4. Inicializar la base y levantar

```bash
# Preparar la base de datos de Chatwoot (solo la primera vez)
docker compose run --rm rails bundle exec rails db:chatwoot_prepare

# Levantar todo
docker compose up -d
```

Chatwoot queda en `127.0.0.1:3000` y n8n en `127.0.0.1:5678` (solo local; el HTTPS lo pone el reverse proxy del paso 5).

## 5. HTTPS con Caddy (reverse proxy)

```bash
apt-get install -y caddy
```

`/etc/caddy/Caddyfile`:

```
chat.tudominio.com {
    reverse_proxy 127.0.0.1:3000
}
n8n.tudominio.com {
    reverse_proxy 127.0.0.1:5678
}
```

```bash
systemctl reload caddy
```

Caddy saca los certificados SSL solo. Apuntá los DNS de los subdominios a la IP del VPS.

## 6. Crear el admin de Chatwoot

Entrá a `https://chat.tudominio.com` y creá la cuenta de administrador (email + contraseña). Ese es el panel donde el equipo de Xelvia atiende y donde vive el **CRM** (Contactos → con etiquetas, notas y atributos).

## 7. Conectar WhatsApp (Coexistencia / Cloud API)

1. En **Chatwoot**: *Configuración → Bandejas de entrada → Agregar → WhatsApp → WhatsApp Cloud*.
2. En **Meta for Developers** (business.facebook.com): activá la **Coexistencia** para el número (así el celular sigue funcionando normal y en paralelo se conecta la API).
3. Copiá de Meta: `Phone Number ID`, `Business Account ID`, `Access Token` (permanente) y pegalos en Chatwoot.
4. Configurá el **webhook** de Meta apuntando a la URL que te da Chatwoot y usá el `Verify Token`.

> La Coexistencia deja que el dueño siga respondiendo desde su WhatsApp normal y, a la vez, que la API automatice. No se pierde el historial.

## 8. Conectar la automatización con IA (n8n)

1. Entrá a `https://n8n.tudominio.com` (usuario/clave del `.env`).
2. *Import from file* → subí `n8n/workflow-whatsapp-ia.json`.
3. En n8n, definí estas variables de entorno / credenciales: `ANTHROPIC_API_KEY`, `CHATWOOT_URL` (ej. `https://chat.tudominio.com`) y `CHATWOOT_API_TOKEN` (Chatwoot → Perfil → Access Token).
4. Copiá la URL del nodo **Webhook** del workflow.
5. En **Chatwoot**: *Configuración → Integraciones → Webhooks* → pegá esa URL y suscribí el evento **`message_created`**.
6. Activá el workflow en n8n.

Listo: cuando un cliente escribe por WhatsApp, Chatwoot lo recibe, n8n lo manda a Claude, Claude responde, se envía por WhatsApp y el contacto queda etiquetado en el CRM.

## 9. Backup (recomendado)

```bash
# Base de datos
docker compose exec postgres pg_dump -U chatwoot chatwoot > backup_$(date +%F).sql
```

Programá un cron semanal para no perder datos.

---

## Costos recurrentes (los paga el cliente)

| Ítem | Costo aprox. |
|------|--------------|
| VPS Hostinger | USD 5-10 / mes |
| WhatsApp Cloud API | Conversaciones iniciadas por el cliente: **gratis**. Plantillas iniciadas por la empresa: costo bajo por conversación |
| Claude (Anthropic) | Pago por uso, centavos por conversación |
| Software (Chatwoot + n8n) | **USD 0** (open source, self-hosted) |
