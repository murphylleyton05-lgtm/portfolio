import type { CatalogProduct, CatalogVariant } from "./types";

type RawVariant = Omit<CatalogVariant, "price"> & { price: number | null };

/** Arma un CatalogProduct con los campos derivados (precio mínimo, stock total). */
export function buildProduct(
  product: Omit<CatalogProduct, "variants" | "minPrice" | "hasPriceRange" | "totalStock">,
  rawVariants: RawVariant[],
): CatalogProduct {
  const variants = [...rawVariants]
    .sort((a, b) => a.position - b.position)
    .map((variant) => ({ ...variant, price: Number(variant.price ?? product.price) }));
  const prices = variants.map((variant) => variant.price);
  const minPrice = prices.length ? Math.min(...prices) : product.price;
  return {
    ...product,
    price: Number(product.price),
    compareAtPrice: product.compareAtPrice === null ? null : Number(product.compareAtPrice),
    variants,
    minPrice,
    hasPriceRange: new Set(prices).size > 1,
    totalStock: variants.reduce((sum, variant) => sum + Math.max(variant.stock, 0), 0),
  };
}
