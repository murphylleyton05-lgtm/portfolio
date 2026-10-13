import { z } from "zod";
import { siteConfig } from "@site-config";
import { normalizeText } from "@/lib/utils";
import type { CatalogProduct } from "./types";

export const SORT_OPTIONS = [
  { value: "destacados", label: "Destacados" },
  { value: "nuevos", label: "Más nuevos" },
  { value: "menor-precio", label: "Menor precio" },
  { value: "mayor-precio", label: "Mayor precio" },
] as const;

export type SortValue = (typeof SORT_OPTIONS)[number]["value"];

type RawParams = Record<string, string | string[] | undefined>;

const first = (value: unknown) => (Array.isArray(value) ? value[0] : value);
const emptyToUndefined = (value: unknown) => {
  const v = first(value);
  return typeof v === "string" && v.trim() === "" ? undefined : v;
};

/** Parámetros de búsqueda del listado (/productos?q=&categoria=&min=&max=&orden=&pagina=&stock=1). */
export const catalogQuerySchema = z.object({
  q: z.preprocess(emptyToUndefined, z.string().trim().max(80).optional()).catch(undefined),
  categoria: z
    .preprocess(
      emptyToUndefined,
      z
        .string()
        .regex(/^[a-z0-9-]{1,80}$/)
        .optional(),
    )
    .catch(undefined),
  min: z.preprocess(emptyToUndefined, z.coerce.number().int().min(0).optional()).catch(undefined),
  max: z.preprocess(emptyToUndefined, z.coerce.number().int().min(0).optional()).catch(undefined),
  orden: z
    .preprocess(emptyToUndefined, z.enum(SORT_OPTIONS.map((o) => o.value) as [SortValue, ...SortValue[]]))
    .catch("destacados"),
  pagina: z.preprocess(emptyToUndefined, z.coerce.number().int().min(1).max(1000)).catch(1),
  stock: z.preprocess(emptyToUndefined, z.literal("1").optional()).catch(undefined),
});

export type CatalogQuery = z.infer<typeof catalogQuerySchema>;

/** Valores inválidos se ignoran (nunca rompe la página por una URL mal armada). */
export function parseCatalogQuery(params: RawParams): CatalogQuery {
  return catalogQuerySchema.parse(params);
}

export type CatalogResult = {
  items: CatalogProduct[];
  total: number;
  page: number;
  pageCount: number;
};

export function queryCatalog(
  products: CatalogProduct[],
  query: CatalogQuery,
  pageSize: number = siteConfig.catalog.productsPerPage,
): CatalogResult {
  const terms = query.q ? normalizeText(query.q).split(/\s+/).filter(Boolean) : [];

  const filtered = products.filter((product) => {
    if (query.categoria && product.category?.slug !== query.categoria) return false;
    if (query.min !== undefined && product.minPrice < query.min) return false;
    if (query.max !== undefined && product.minPrice > query.max) return false;
    if (query.stock && product.totalStock <= 0) return false;
    if (terms.length) {
      const haystack = normalizeText(
        [
          product.name,
          product.description,
          product.category?.name ?? "",
          ...product.variants.map((v) => v.sku ?? ""),
        ].join(" "),
      );
      if (!terms.every((term) => haystack.includes(term))) return false;
    }
    return true;
  });

  const byNewest = (a: CatalogProduct, b: CatalogProduct) => b.createdAt.localeCompare(a.createdAt);
  const sorted = [...filtered].sort((a, b) => {
    switch (query.orden) {
      case "menor-precio":
        return a.minPrice - b.minPrice || byNewest(a, b);
      case "mayor-precio":
        return b.minPrice - a.minPrice || byNewest(a, b);
      case "nuevos":
        return byNewest(a, b);
      default: {
        // Con stock primero, después destacados, después más nuevos.
        const inStock = Number(b.totalStock > 0) - Number(a.totalStock > 0);
        const featured = Number(b.featured) - Number(a.featured);
        return inStock || featured || byNewest(a, b);
      }
    }
  });

  const pageCount = Math.max(1, Math.ceil(sorted.length / pageSize));
  const page = Math.min(query.pagina, pageCount);
  return {
    items: sorted.slice((page - 1) * pageSize, page * pageSize),
    total: sorted.length,
    page,
    pageCount,
  };
}

/** Arma la URL del listado conservando filtros y cambiando solo lo indicado. */
export function catalogHref(
  query: Partial<CatalogQuery>,
  changes: Partial<Record<keyof CatalogQuery, string | number | undefined>> = {},
) {
  const merged: Record<string, string | number | undefined> = { ...query, ...changes };
  if (merged.orden === "destacados") delete merged.orden;
  if (merged.pagina === 1 || merged.pagina === "1") delete merged.pagina;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(merged)) {
    if (value !== undefined && value !== "") params.set(key, String(value));
  }
  const search = params.toString();
  return search ? `/productos?${search}` : "/productos";
}
