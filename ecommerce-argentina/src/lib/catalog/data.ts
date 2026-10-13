import "server-only";
import { cacheLife, cacheTag } from "next/cache";
import { isSupabaseConfigured } from "@/lib/env";
import { createPublicClient } from "@/lib/supabase/public";
import { buildProduct } from "./build";
import { getDemoCatalog } from "./demo";
import type { Catalog, CatalogProduct } from "./types";

/** Tag para invalidar el catálogo cacheado (admin y webhook de pagos). */
export const CATALOG_TAG = "catalog";

/**
 * Todo el catálogo activo, cacheado. Para una tienda chica/mediana (hasta un
 * par de miles de productos) es más simple y rápido filtrar en memoria que
 * hacer una consulta por cada combinación de filtros. Ver DECISIONS.md.
 */
export async function getCatalog(): Promise<Catalog> {
  "use cache";
  // Se refresca cada minuto (stock que cambia por ventas) y al instante cuando
  // el admin guarda cambios (updateTag/revalidateTag).
  cacheLife("minutes");
  cacheTag(CATALOG_TAG);

  if (!isSupabaseConfigured) return getDemoCatalog();

  const supabase = createPublicClient();
  const [categoriesResult, productsResult] = await Promise.all([
    supabase.from("categories").select("id, name, slug, description, position").order("position").order("name"),
    supabase
      .from("products")
      .select(
        "id, slug, name, description, price, compare_at_price, images, featured, created_at, category:categories(id, name, slug), variants:product_variants(id, name, sku, price, stock, position)",
      )
      .eq("active", true)
      .order("created_at", { ascending: false }),
  ]);

  if (categoriesResult.error) throw new Error(`No se pudieron leer las categorías: ${categoriesResult.error.message}`);
  if (productsResult.error) throw new Error(`No se pudieron leer los productos: ${productsResult.error.message}`);

  const products = productsResult.data
    .filter((row) => row.variants.length > 0)
    .map((row) =>
      buildProduct(
        {
          id: row.id,
          slug: row.slug,
          name: row.name,
          description: row.description,
          price: row.price,
          compareAtPrice: row.compare_at_price,
          images: row.images,
          featured: row.featured,
          createdAt: row.created_at,
          category: row.category,
        },
        row.variants,
      ),
    );

  return { categories: categoriesResult.data, products };
}

export async function getProductBySlug(slug: string): Promise<CatalogProduct | null> {
  const { products } = await getCatalog();
  return products.find((product) => product.slug === slug) ?? null;
}

/** Destacados con stock primero; si faltan, completa con el resto del catálogo. */
export async function getFeaturedProducts(limit = 8): Promise<CatalogProduct[]> {
  const { products } = await getCatalog();
  const score = (product: CatalogProduct) => Number(product.totalStock > 0) * 2 + Number(product.featured);
  return [...products].sort((a, b) => score(b) - score(a)).slice(0, limit);
}

export async function getRelatedProducts(product: CatalogProduct, limit = 4): Promise<CatalogProduct[]> {
  const { products } = await getCatalog();
  const others = products.filter((p) => p.id !== product.id);
  const sameCategory = others.filter((p) => p.category?.id && p.category.id === product.category?.id);
  return [...sameCategory, ...others.filter((p) => !sameCategory.includes(p))].slice(0, limit);
}
