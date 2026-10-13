"use server";

import { z } from "zod";
import { getLiveVariants } from "@/lib/catalog/live";
import { cartLineSchema } from "@/lib/checkout/schema";

const refreshSchema = z.array(cartLineSchema.extend({ quantity: z.int().min(0).max(999) })).max(50);

export type RefreshedLine = {
  variantId: string;
  productId: string;
  slug: string;
  name: string;
  variantName: string;
  price: number;
  stock: number;
  image: string | null;
};

/**
 * Devuelve precio y stock actuales de las variantes del carrito. Las que ya no
 * existen o están pausadas no vuelven (el cliente las saca del carrito).
 */
export async function refreshCart(
  lines: unknown,
): Promise<{ ok: true; lines: RefreshedLine[] } | { ok: false; error: string }> {
  const parsed = refreshSchema.safeParse(lines);
  if (!parsed.success) return { ok: false, error: "Carrito inválido." };
  try {
    const live = await getLiveVariants(parsed.data.map((line) => line.variantId));
    return {
      ok: true,
      lines: [...live.values()].map((line) => ({
        variantId: line.variantId,
        productId: line.productId,
        slug: line.slug,
        name: line.name,
        variantName: line.variantName,
        price: line.price,
        stock: line.stock,
        image: line.image,
      })),
    };
  } catch (error) {
    console.error("[refreshCart]", error);
    return { ok: false, error: "No pudimos actualizar el carrito. Probá de nuevo." };
  }
}
