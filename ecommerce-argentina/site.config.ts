/**
 * Identidad y reglas de negocio de la tienda.
 *
 * Este es el ÚNICO archivo que tenés que tocar para cambiar marca, colores,
 * logo, contacto, redes, envíos y retiro. Todo lo que dice "CAMBIAR" son datos
 * de ejemplo. Las claves secretas (Supabase, Mercado Pago, Resend) NO van acá:
 * van en `.env.local` (ver `.env.example`).
 */

export type ShippingZone = {
  /** Identificador interno (se guarda en el pedido). */
  id: string;
  /** Nombre que ve el cliente. */
  name: string;
  /**
   * Rangos de códigos postales numéricos (4 dígitos), ambos inclusive.
   * Para CPA tipo "C1425ABC" se usan los 4 números del medio.
   */
  postalCodeRanges: Array<[number, number]>;
  /** Costo en pesos. */
  cost: number;
  /** Texto de demora estimada. */
  eta: string;
};

export const siteConfig = {
  // ── Marca ────────────────────────────────────────────────────────────────
  name: "Pampa Store", // CAMBIAR
  shortName: "Pampa", // CAMBIAR (se usa en el ícono de la app y en el resumen de tarjeta)
  tagline: "Básicos de calidad, hechos en Argentina", // CAMBIAR
  description:
    "Indumentaria y accesorios minimalistas. Envíos a todo el país y retiro sin cargo. Pagá con Mercado Pago en cuotas.", // CAMBIAR
  /** Logo en /public. Poné `null` para mostrar solo el nombre en texto. */
  logo: { src: "/logo.svg", alt: "Pampa Store", width: 32, height: 32 } as {
    src: string;
    alt: string;
    width: number;
    height: number;
  } | null,
  /** Imagen por defecto para compartir en redes (1200x630). Si es null se genera una automáticamente. */
  ogImage: null as string | null,
  keywords: ["indumentaria", "remeras", "buzos", "accesorios", "tienda online", "Argentina"],

  // ── Colores (cualquier color CSS válido) ─────────────────────────────────
  colors: {
    /** Botones principales, links destacados. */
    primary: "#18181b",
    /** Texto sobre `primary`. */
    primaryForeground: "#ffffff",
    /** Ofertas, badges, detalles. */
    accent: "#c2410c",
    accentForeground: "#ffffff",
    /** Fondo general y texto. */
    background: "#ffffff",
    foreground: "#18181b",
    /** Fondos suaves (tarjetas, inputs). */
    muted: "#f4f4f5",
    mutedForeground: "#71717a",
    border: "#e4e4e7",
  },

  // ── Localización ─────────────────────────────────────────────────────────
  locale: "es-AR",
  currency: "ARS",
  timeZone: "America/Argentina/Buenos_Aires",

  // ── Contacto ─────────────────────────────────────────────────────────────
  contact: {
    email: "hola@pampastore.com.ar", // CAMBIAR (también recibe el aviso de cada venta)
    phone: "+54 9 11 2345-6789", // CAMBIAR
    /** WhatsApp en formato internacional, solo números (549 + característica sin 0 + número sin 15). */
    whatsapp: "5491123456789", // CAMBIAR
    whatsappDefaultMessage: "¡Hola! Tengo una consulta sobre la tienda.",
    address: "Av. Corrientes 1234, CABA", // CAMBIAR
  },

  // ── Redes (dejá en "" las que no uses) ───────────────────────────────────
  social: {
    instagram: "https://instagram.com/pampastore", // CAMBIAR
    facebook: "",
    tiktok: "",
    x: "",
  },

  // ── Envíos ───────────────────────────────────────────────────────────────
  shipping: {
    enabled: true,
    /** Desde este subtotal el envío es gratis. `null` para desactivar. */
    freeShippingThreshold: 150000 as number | null,
    /**
     * Zonas por código postal. Se evalúan en orden: gana la primera que matchee.
     * Si ninguna matchea, se usa `defaultZone`.
     */
    zones: [
      { id: "caba", name: "CABA", postalCodeRanges: [[1000, 1499]], cost: 4500, eta: "24 a 48 hs hábiles" },
      { id: "gba", name: "GBA", postalCodeRanges: [[1600, 1999]], cost: 6500, eta: "48 a 72 hs hábiles" },
    ] as ShippingZone[],
    defaultZone: { id: "interior", name: "Resto del país", cost: 9900, eta: "3 a 7 días hábiles" },
  },

  // ── Retiro en persona ────────────────────────────────────────────────────
  pickup: {
    enabled: true,
    label: "Retiro en el local (sin cargo)",
    address: "Av. Corrientes 1234, CABA", // CAMBIAR
    hours: "Lunes a viernes de 10 a 18 hs", // CAMBIAR
    instructions: "Te avisamos por email cuando tu pedido esté listo para retirar.",
  },

  // ── Pagos ────────────────────────────────────────────────────────────────
  payments: {
    /** Cuotas máximas a ofrecer en Mercado Pago. */
    maxInstallments: 6,
    /** Texto que aparece en el resumen de la tarjeta del cliente (máx. 13 caracteres). */
    statementDescriptor: "PAMPASTORE", // CAMBIAR
    /** Texto promocional junto al precio. Dejá "" para ocultarlo. */
    installmentsBanner: "Hasta 6 cuotas con Mercado Pago",
  },

  // ── Catálogo ─────────────────────────────────────────────────────────────
  catalog: {
    productsPerPage: 12,
    /** Debajo de este stock se marca "últimas unidades" y se resalta en el admin. */
    lowStockThreshold: 3,
  },

  // ── Legales (Argentina) ──────────────────────────────────────────────────
  legal: {
    /** Razón social y CUIT que se muestran en el pie. */
    businessName: "Pampa Store S.R.L.", // CAMBIAR
    cuit: "30-00000000-0", // CAMBIAR
    /**
     * Link del QR "Data Fiscal" de AFIP/ARCA (obligatorio para vender online).
     * Lo generás en arca.gob.ar → "Data Fiscal". Dejalo en "" hasta tenerlo.
     */
    dataFiscalUrl: "", // CAMBIAR
    /** Días para arrepentirse de una compra online (Ley 24.240, art. 34). */
    withdrawalDays: 10,
  },
} as const;

export type SiteConfig = typeof siteConfig;
