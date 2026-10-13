import "server-only";
import { isSupabaseConfigured } from "@/lib/env";
import { createPublicClient } from "@/lib/supabase/public";
import { getDemoCatalog } from "./demo";

/** Datos actuales de una variante, leídos SIN caché (precio y stock reales). */
export type LiveVariant = {
  variantId: string;
  productId: string;
  slug: string;
  name: string;
  variantName: string;
  sku: string | null;
  price: number;
  stock: number;
  image: string | null;
};

/**
 * Devuelve solo variantes vendibles (producto activo). Se usa para refrescar el
 * carrito y para armar el pedido con precios del servidor.
 */
export async function getLiveVariants(variantIds: string[]): Promise<Map<string, LiveVariant>> {
  const ids = [...new Set(variantIds)];
  const result = new Map<string, LiveVariant>();
  if (!ids.length) return result;

  if (!isSupabaseConfigured) {
    for (const product of getDemoCatalog().products) {
      for (const variant of product.variants) {
        if (!ids.includes(variant.id)) continue;
        result.set(variant.id, {
          variantId: variant.id,
          productId: product.id,
          slug: product.slug,
          name: product.name,
          variantName: variant.name,
          sku: variant.sku,
          price: variant.price,
          stock: variant.stock,
          image: product.images[0] ?? null,
        });
      }
    }
    return result;
  }

  // Cliente anónimo: RLS solo devuelve variantes de productos activos.
  const supabase = createPublicClient();
  const { data, error } = await supabase
    .from("product_variants")
    .select("id, name, sku, price, stock, product:products!inner(id, slug, name, price, images, active)")
    .in("id", ids);
  if (error) throw new Error(`No se pudo verificar el stock: ${error.message}`);

  for (const row of data) {
    if (!row.product.active) continue;
    result.set(row.id, {
      variantId: row.id,
      productId: row.product.id,
      slug: row.product.slug,
      name: row.product.name,
      variantName: row.name,
      sku: row.sku,
      price: Number(row.price ?? row.product.price),
      stock: row.stock,
      image: row.product.images[0] ?? null,
    });
  }
  return result;
}
