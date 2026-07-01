# Guía de ensayo — Practicá antes de tocar el server del cliente

> Regla de oro: **no despliegues en el servidor de Marcos por primera vez.**
> Hacé este ensayo completo en un VPS de prueba tuyo. Cuando lo repitas en lo
> real, va a salir en la mitad de tiempo y sin sustos.

## Por qué ensayar

- Aprendés el flujo sin presión ni cliente mirando.
- Descubrís los errores en tu server, no en el de él.
- Podés **grabar la pantalla** y usarlo como demo/testimonio.
- Llegás a la instalación real con seguridad total.

Costo del ensayo: un VPS chico ~USD 7 que cancelás después. Es la mejor inversión de todo el proyecto.

---

## Paso 0 — Chequeo previo (lo más importante)

Antes que nada, verificá el punto más riesgoso: **la Coexistencia de WhatsApp.**

- El número de Marcos tiene que estar en la **app de WhatsApp Business** (no el WhatsApp común).
- Tiene que tener **movimiento real** (chats recientes).
- La Coexistencia tiene que estar disponible en su región y versión de app.

👉 Confirmá esto con Marcos ANTES de arrancar. Si el número no califica, se resuelve, pero mejor saberlo el día 1 y no el día 3.

---

## Paso 1 — Conseguir un VPS de prueba

1. Entrá a Hostinger (o cualquier VPS) y contratá el plan más chico con **Ubuntu 22.04** (2 GB RAM mínimo).
2. Anotá la **IP** y la **contraseña de root** que te dan.
3. Opcional pero recomendado: un dominio o subdominio de prueba apuntando a esa IP.

## Paso 2 — Entrar al servidor

Desde tu compu (terminal) o desde el **navegador de Hostinger** (Browser terminal):

```bash
ssh root@TU_IP
```

Metés la contraseña. Ya estás adentro.

## Paso 3 — Seguir el INSTALL.md

Abrí [INSTALL.md](./INSTALL.md) y andá paso por paso. Marcá cada uno cuando termine:

- [ ] Docker instalado (`docker --version` responde)
- [ ] Repo clonado y `.env` completado
- [ ] `docker compose run --rm rails ... db:chatwoot_prepare` sin errores
- [ ] `docker compose up -d` y `docker compose ps` muestra todo "Up"
- [ ] Caddy con HTTPS andando
- [ ] Entrás a `https://chat.tudominio.com` y ves el login de Chatwoot
- [ ] Creaste el usuario admin
- [ ] Entrás a n8n en `https://n8n.tudominio.com`
- [ ] Importaste el workflow y quedó activo

## Paso 4 — Probar la automatización SIN WhatsApp todavía

Antes de enchufar WhatsApp, probá que la IA responde:

1. En Chatwoot creá una conversación de prueba manual (canal "API" o "Website").
2. Escribí un mensaje como cliente.
3. Verificá que n8n se dispara, Claude responde y el mensaje vuelve a Chatwoot con la etiqueta puesta.

Si eso funciona, el cerebro del sistema ya está. Lo demás es conectar el caño de WhatsApp.

## Paso 5 — Conectar WhatsApp (con un número tuyo de prueba)

Usá un número tuyo para el ensayo, no el de Marcos. Seguí el paso 7 del INSTALL. Cuando te escribas a vos mismo y el sistema responda solo, **ganaste**.

## Paso 6 — Grabá la demo

Con todo andando, grabá un video corto mostrando: llega un mensaje → responde la IA → aparece el contacto en el CRM. Ese video vale oro para mostrarle a Marcos y a los próximos clientes.

## Paso 7 — Apagar el ensayo

```bash
docker compose down
```

Cancelá el VPS de prueba. Ya sabés hacerlo con los ojos cerrados.

---

## Errores comunes y solución rápida

| Síntoma | Causa probable | Solución |
|---|---|---|
| Chatwoot no abre | Migración no corrió | Repetir `docker compose run --rm rails ... db:chatwoot_prepare` |
| "502" en el dominio | Caddy no conecta al contenedor | Revisar puertos y que `rails` esté "Up" |
| n8n no recibe el webhook | URL mal cargada en Chatwoot | Copiar de nuevo la URL del nodo Webhook |
| La IA no responde | Falta `ANTHROPIC_API_KEY` en n8n | Cargar la credencial y reactivar el workflow |
| WhatsApp no llega | Webhook de Meta mal configurado | Revisar Verify Token y la URL en Meta |

Ante cualquiera de estos, mandame el error y lo resolvemos al toque.
