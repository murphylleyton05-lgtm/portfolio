/**
 * Genera, a partir de src/data/demo-catalog.ts:
 *   - supabase/seed.sql                  (categorías, productos y variantes)
 *   - public/placeholders/<slug>-{1,2}.svg (imágenes placeholder livianas)
 *
 * Uso: npm run demo:generate
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import {
  demoCategories,
  demoCreatedAt,
  demoImages,
  demoProducts,
  type DemoProduct,
} from "../src/data/demo-catalog";

const root = join(import.meta.dirname, "..");

// ── Seed SQL ────────────────────────────────────────────────────────────────

const sql = (value: string | number | boolean | null | undefined): string => {
  if (value === null || value === undefined) return "null";
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return `'${value.replace(/'/g, "''")}'`;
};

const sqlArray = (values: string[]) =>
  values.length ? `array[${values.map(sql).join(", ")}]::text[]` : "'{}'::text[]";

function buildSeed() {
  const lines: string[] = [
    "-- ════════════════════════════════════════════════════════════════════════",
    "-- Datos de ejemplo: 4 categorías y 12 productos con variantes y stock.",
    "-- ARCHIVO GENERADO por `npm run demo:generate` desde src/data/demo-catalog.ts",
    "-- Se puede correr varias veces (no duplica). Borrá los productos desde el",
    "-- admin cuando cargues los tuyos.",
    "-- ════════════════════════════════════════════════════════════════════════",
    "",
    "insert into public.categories (id, name, slug, description, position) values",
    demoCategories
      .map((c) => `  (${sql(c.id)}, ${sql(c.name)}, ${sql(c.slug)}, ${sql(c.description)}, ${c.position})`)
      .join(",\n") + "\non conflict (id) do nothing;",
    "",
    "insert into public.products (id, category_id, name, slug, description, price, compare_at_price, images, active, featured, created_at) values",
    demoProducts
      .map((p, index) => {
        const category = demoCategories.find((c) => c.slug === p.categorySlug);
        if (!category) throw new Error(`Categoría inexistente: ${p.categorySlug}`);
        return `  (${[
          sql(p.id),
          sql(category.id),
          sql(p.name),
          sql(p.slug),
          sql(p.description),
          p.price.toFixed(2),
          p.compareAtPrice ? p.compareAtPrice.toFixed(2) : "null",
          sqlArray(demoImages(p.slug)),
          "true",
          String(Boolean(p.featured)),
          `${sql(demoCreatedAt(index))}::timestamptz`,
        ].join(", ")})`;
      })
      .join(",\n") + "\non conflict (id) do nothing;",
    "",
    "insert into public.product_variants (id, product_id, name, sku, price, stock, position) values",
    demoProducts
      .flatMap((p) =>
        p.variants.map(
          (v, index) =>
            `  (${sql(v.id)}, ${sql(p.id)}, ${sql(v.name)}, ${sql(v.sku)}, ${v.price ? v.price.toFixed(2) : "null"}, ${v.stock}, ${index})`,
        ),
      )
      .join(",\n") + "\non conflict (id) do nothing;",
    "",
  ];
  return lines.join("\n");
}

// ── Placeholders SVG ────────────────────────────────────────────────────────

const shapes: Record<DemoProduct["shape"], (fg: string, bg: string) => string> = {
  tshirt: (fg) =>
    `<path fill="${fg}" d="M120 60 160 40q40 30 80 0l40 20 70 50-30 60-30-15v185H110V155l-30 15-30-60z"/>`,
  tank: (fg) =>
    `<path fill="${fg}" d="M140 40q10 70-20 100v200h160V140q-30-30-20-100h-30q-30 50-60 0z"/>`,
  hoodie: (fg, bg) =>
    `<path fill="${fg}" d="M150 70q0-50 50-50t50 50l50 20 60 190-40 15-35-125v180H115V170L80 295l-40-15 60-190z"/>` +
    `<ellipse cx="200" cy="72" rx="32" ry="38" fill="${bg}" opacity=".35"/>` +
    `<path fill="${bg}" opacity=".25" d="M150 250h100l15 70H135z"/>`,
  sweater: (fg, bg) =>
    `<path fill="${fg}" d="M150 50q50 30 100 0l50 20 60 210-40 15-35-135v190H115V160L80 295l-40-15 60-210z"/>` +
    `<path fill="none" stroke="${bg}" stroke-opacity=".3" stroke-width="6" d="M118 330h164"/>`,
  jacket: (fg, bg) =>
    `<path fill="${fg}" d="M150 50q50 30 100 0l50 20 60 210-40 15-35-135v190H115V160L80 295l-40-15 60-210z"/>` +
    `<path stroke="${bg}" stroke-opacity=".55" stroke-width="5" d="M200 62v288"/>` +
    `<path fill="${bg}" opacity=".3" d="m150 50 50 40 50-40-10-15q-40 25-80 0z"/>`,
  pants: (fg, bg) =>
    `<path fill="${fg}" d="M130 40h140l20 320h-70l-20-220-20 220h-70z"/>` +
    `<path stroke="${bg}" stroke-opacity=".35" stroke-width="5" d="M132 62h136"/>`,
  cap: (fg, bg) =>
    `<path fill="${fg}" d="M110 220q0-110 90-110t90 110z"/>` +
    `<path fill="${fg}" d="M100 215h200q60 5 50 30H110z"/>` +
    `<circle cx="200" cy="114" r="8" fill="${bg}" opacity=".5"/>`,
  bag: (fg) =>
    `<path fill="none" stroke="${fg}" stroke-width="14" d="M150 160q0-100 50-100t50 100"/>` +
    `<path fill="${fg}" d="M110 150h180l20 200H90z"/>`,
  socks: (fg) =>
    `<path fill="${fg}" opacity=".45" d="M120 60h60v200q0 20 20 30l60 20q30 15 20 45-10 20-40 15l-90-20q-30-10-30-40z"/>` +
    `<path fill="${fg}" d="M170 40h60v210q0 20 20 30l60 20q30 15 20 45-10 20-40 15l-90-20q-30-10-30-40z"/>`,
  mate: (fg, bg) =>
    `<path stroke="#a1a1aa" stroke-width="9" stroke-linecap="round" d="m212 150 60-110"/>` +
    `<path fill="${fg}" d="M140 140q-20 120 20 190 40 30 80 0 40-70 20-190z"/>` +
    `<ellipse cx="200" cy="140" rx="62" ry="16" fill="${bg}" opacity=".45"/>`,
};

function mix(hexA: string, hexB: string, weight: number) {
  const parse = (hex: string) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
  const [a, b] = [parse(hexA), parse(hexB)];
  return `#${a
    .map((channel, i) => Math.round(channel * (1 - weight) + b[i] * weight).toString(16).padStart(2, "0"))
    .join("")}`;
}

const escapeXml = (text: string) =>
  text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function placeholderSvg(product: DemoProduct, detail: boolean) {
  const [bg, fg] = product.palette;
  const background = detail ? mix(bg, fg, 0.12) : bg;
  const shape = shapes[product.shape](fg, background);
  // Vista 1: prenda completa. Vista 2: "detalle" con zoom.
  const transform = detail ? "translate(60 120) scale(1.7)" : "translate(160 210) scale(1.2)";
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 1000" width="800" height="1000" role="img" aria-label="${escapeXml(product.name)}">
<rect width="800" height="1000" fill="${background}"/>
<g transform="${transform}">${shape}</g>
<text x="400" y="930" fill="${fg}" fill-opacity=".7" font-family="ui-sans-serif, system-ui, sans-serif" font-size="30" text-anchor="middle" letter-spacing="2">${escapeXml(product.name.toUpperCase())}</text>
</svg>
`;
}

// ── Escribir archivos ───────────────────────────────────────────────────────

writeFileSync(join(root, "supabase", "seed.sql"), buildSeed());

const placeholdersDir = join(root, "public", "placeholders");
mkdirSync(placeholdersDir, { recursive: true });
for (const product of demoProducts) {
  const [first, second] = demoImages(product.slug);
  writeFileSync(join(root, "public", first), placeholderSvg(product, false));
  writeFileSync(join(root, "public", second), placeholderSvg(product, true));
}

console.log(`✓ seed.sql y ${demoProducts.length * 2} placeholders generados`);
