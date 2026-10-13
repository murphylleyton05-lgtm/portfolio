# Decisiones

Registro de decisiones tomadas sin consultar, eligiendo siempre la opción más
simple que resuelve el problema. Si alguna no te sirve, cada punto dice dónde
cambiarla.

## Proyecto

- **Carpeta propia dentro del monorepo `portfolio`** (`ecommerce-argentina/`). En
  Vercel hay que poner *Root Directory = `ecommerce-argentina`*.
- **Next.js 16.4 con Cache Components** (lo que trae `create-next-app` por
  defecto). El catálogo se cachea con `"use cache"` + `cacheTag("catalog")` y se
  invalida cuando el admin guarda cambios o entra un pago. Lo que depende del
  request (carrito, pedido, admin) va dentro de `<Suspense>`.
- **`site.config.ts` en la raíz** con alias `@site-config`. Ahí está todo lo
  que no es secreto: marca, colores, contacto, redes, envíos, retiro y cuotas.
  Los secretos van en `.env.local`.
- **Colores por variables CSS**: el layout raíz inyecta `--brand-*` desde
  `site.config.ts` y Tailwind los usa como `bg-primary`, `text-accent`, etc.
  No hay modo oscuro (la marca define su paleta).
- **Favicon y apple-icon generados** con la inicial de `shortName` y el color
  primario, así cambian solos al cambiar la config. El logo del header es
  `public/logo.svg` (reemplazalo o poné `logo: null`).
- **Modo demo**: si faltan las variables de Supabase, la tienda muestra el
  catálogo de ejemplo desde `src/data/demo-catalog.ts` (los mismos 12 productos
  del seed). El checkout y el admin muestran un aviso pidiendo configurar
  Supabase. Así `npm run dev` funciona desde el minuto uno.
- **`NEXT_PUBLIC_SITE_URL` opcional en Vercel**: si no está, se usa
  `VERCEL_PROJECT_PRODUCTION_URL`.
- **Headers de seguridad básicos** en `next.config.ts` (nosniff, referrer,
  frame-options, permissions-policy). No se agregó CSP estricta para no romper
  el checkout de Mercado Pago ni scripts de terceros que quieras sumar.
- **`npm audit`** reporta 5 vulnerabilidades *high* en `braces`/`micromatch`,
  dependencias de desarrollo de `eslint-config-next`. No llegan al bundle de
  producción y la única "solución" automática es bajar a Next 14, así que se
  dejaron.
