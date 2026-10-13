/**
 * Catálogo de ejemplo. Es la ÚNICA fuente de los 12 productos demo:
 *  - `npm run db:seed:generate` lo convierte en `supabase/seed.sql`.
 *  - Sin Supabase configurado, la tienda lo muestra directamente (modo demo).
 * Los IDs son fijos para que el carrito siga funcionando al pasar de demo a Supabase.
 */

export type DemoCategory = {
  id: string;
  name: string;
  slug: string;
  description: string;
  position: number;
};

export type DemoVariant = {
  id: string;
  name: string;
  sku: string;
  stock: number;
  price?: number;
};

export type DemoProduct = {
  id: string;
  categorySlug: string;
  name: string;
  slug: string;
  description: string;
  price: number;
  compareAtPrice?: number;
  featured?: boolean;
  /** Colores del placeholder SVG: [fondo, prenda]. */
  palette: [string, string];
  /** Silueta del placeholder. */
  shape: "tshirt" | "tank" | "hoodie" | "sweater" | "jacket" | "pants" | "cap" | "bag" | "socks" | "mate";
  variants: DemoVariant[];
};

const categoryId = (n: number) => `10000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const productId = (n: number) => `20000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const variantId = (product: number, variant: number) =>
  `30000000-0000-4000-8000-${String(product * 100 + variant).padStart(12, "0")}`;

export const demoCategories: DemoCategory[] = [
  { id: categoryId(1), name: "Remeras", slug: "remeras", description: "Remeras y musculosas de algodón.", position: 1 },
  { id: categoryId(2), name: "Buzos y camperas", slug: "buzos-y-camperas", description: "Abrigo para todos los días.", position: 2 },
  { id: categoryId(3), name: "Pantalones", slug: "pantalones", description: "Joggers y jeans de calce cómodo.", position: 3 },
  { id: categoryId(4), name: "Accesorios", slug: "accesorios", description: "Gorras, bolsos, medias y más.", position: 4 },
];

function sizes(product: number, prefix: string, list: Array<[string, number]>): DemoVariant[] {
  return list.map(([name, stock], index) => ({
    id: variantId(product, index + 1),
    name,
    sku: `${prefix}-${name.replace(/\s+/g, "").toUpperCase()}`,
    stock,
  }));
}

export const demoProducts: DemoProduct[] = [
  {
    id: productId(1),
    categorySlug: "remeras",
    name: "Remera Básica Algodón",
    slug: "remera-basica-algodon",
    description:
      "La remera que vas a usar todos los días. Jersey de algodón peinado 24/1, cuello redondo con ribb y costuras reforzadas. Calce regular, no se deforma con los lavados.",
    price: 24990,
    featured: true,
    palette: ["#f4efe6", "#2f2f2f"],
    shape: "tshirt",
    variants: sizes(1, "REM-BAS", [["S", 10], ["M", 15], ["L", 12], ["XL", 6]]),
  },
  {
    id: productId(2),
    categorySlug: "remeras",
    name: "Remera Oversize Estampada",
    slug: "remera-oversize-estampada",
    description:
      "Corte oversize con hombro caído y estampa frontal en serigrafía al agua. Algodón 100% de 180 g, suave y con buena caída.",
    price: 29990,
    compareAtPrice: 34990,
    palette: ["#e8eef2", "#1e3a5f"],
    shape: "tshirt",
    variants: sizes(2, "REM-OVS", [["S", 4], ["M", 8], ["L", 7], ["XL", 2]]),
  },
  {
    id: productId(3),
    categorySlug: "remeras",
    name: "Musculosa Deportiva Dry-Fit",
    slug: "musculosa-deportiva-dry-fit",
    description:
      "Tela técnica liviana que seca rápido y no se pega al cuerpo. Ideal para entrenar o salir a correr en verano.",
    price: 19990,
    palette: ["#eef3ea", "#3f6212"],
    shape: "tank",
    variants: sizes(3, "MUS-DRY", [["S", 9], ["M", 11], ["L", 5]]),
  },
  {
    id: productId(4),
    categorySlug: "buzos-y-camperas",
    name: "Buzo Canguro Frisa",
    slug: "buzo-canguro-frisa",
    description:
      "Buzo con capucha y bolsillo canguro en frisa invisible de algodón. Puños y cintura con elastano para que mantenga la forma.",
    price: 54990,
    featured: true,
    palette: ["#ece9f3", "#3b3363"],
    shape: "hoodie",
    variants: sizes(4, "BUZ-CAN", [["S", 5], ["M", 9], ["L", 8], ["XL", 3]]),
  },
  {
    id: productId(5),
    categorySlug: "buzos-y-camperas",
    name: "Buzo Cuello Redondo Liso",
    slug: "buzo-cuello-redondo-liso",
    description: "Clásico buzo de frisa sin capucha. Va con todo: jeans, joggers o arriba de una camisa.",
    price: 47990,
    palette: ["#f3ece4", "#7c5a3a"],
    shape: "sweater",
    variants: sizes(5, "BUZ-RED", [["S", 6], ["M", 7], ["L", 6], ["XL", 4]]),
  },
  {
    id: productId(6),
    categorySlug: "buzos-y-camperas",
    name: "Campera Rompeviento",
    slug: "campera-rompeviento",
    description:
      "Campera liviana repelente al agua, con capucha guardable en el cuello y bolsillos con cierre. Se pliega en su propio bolsillo.",
    price: 69990,
    compareAtPrice: 79990,
    featured: true,
    palette: ["#e6f0ef", "#0f4c45"],
    shape: "jacket",
    variants: sizes(6, "CAM-ROM", [["M", 4], ["L", 5], ["XL", 2]]),
  },
  {
    id: productId(7),
    categorySlug: "pantalones",
    name: "Jogger Frisa",
    slug: "jogger-frisa",
    description: "Jogger de frisa con cintura elástica y cordón, bolsillos laterales y puño en el tobillo.",
    price: 44990,
    palette: ["#ececec", "#3a3a3a"],
    shape: "pants",
    variants: sizes(7, "JOG-FRI", [["S", 7], ["M", 10], ["L", 8], ["XL", 4]]),
  },
  {
    id: productId(8),
    categorySlug: "pantalones",
    name: "Jean Recto Clásico",
    slug: "jean-recto-clasico",
    description: "Denim rígido 12 oz de corte recto y tiro medio. Cinco bolsillos y botón metálico.",
    price: 64990,
    palette: ["#e7edf6", "#27467a"],
    shape: "pants",
    variants: sizes(8, "JEA-REC", [["38", 3], ["40", 6], ["42", 6], ["44", 4], ["46", 2]]),
  },
  {
    id: productId(9),
    categorySlug: "accesorios",
    name: "Gorra Trucker",
    slug: "gorra-trucker",
    description: "Gorra con frente de gabardina, red trasera y cierre regulable a presión. Talle único.",
    price: 18990,
    palette: ["#f6ebe7", "#9a3412"],
    shape: "cap",
    variants: [{ id: variantId(9, 1), name: "Único", sku: "GOR-TRU", stock: 20 }],
  },
  {
    id: productId(10),
    categorySlug: "accesorios",
    name: "Tote Bag de Lona",
    slug: "tote-bag-de-lona",
    description: "Bolso de lona natural reforzada con manijas largas y bolsillo interno. Entra la notebook.",
    price: 15990,
    featured: true,
    palette: ["#f5f1e8", "#8a7350"],
    shape: "bag",
    variants: [{ id: variantId(10, 1), name: "Único", sku: "TOT-LON", stock: 25 }],
  },
  {
    id: productId(11),
    categorySlug: "accesorios",
    name: "Pack x3 Medias de Algodón",
    slug: "pack-x3-medias-de-algodon",
    description: "Tres pares de medias de caña media con puño suave y talón reforzado. Colores surtidos.",
    price: 9990,
    palette: ["#eef2f6", "#475569"],
    shape: "socks",
    variants: sizes(11, "MED-PK3", [["35 a 39", 18], ["40 a 44", 2]]),
  },
  {
    id: productId(12),
    categorySlug: "accesorios",
    name: "Mate de Calabaza con Bombilla",
    slug: "mate-de-calabaza-con-bombilla",
    description:
      "Mate de calabaza forrado en cuero con virola de alpaca y bombilla de acero inoxidable. Viene curado y listo para usar.",
    price: 27990,
    featured: true,
    palette: ["#f1efe4", "#5b4a2a"],
    shape: "mate",
    variants: [{ id: variantId(12, 1), name: "Único", sku: "MAT-CAL", stock: 0 }],
  },
];

/** Rutas de las imágenes placeholder generadas en /public/placeholders. */
export function demoImages(slug: string) {
  return [`/placeholders/${slug}-1.svg`, `/placeholders/${slug}-2.svg`];
}

/** Fecha de alta escalonada para que "Más nuevos" tenga un orden estable. */
export function demoCreatedAt(index: number) {
  return new Date(Date.UTC(2026, 9, 1, 12, 0, 0) + index * 3_600_000).toISOString();
}
