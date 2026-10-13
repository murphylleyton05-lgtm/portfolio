import { demoCategories, demoCreatedAt, demoImages, demoProducts } from "@/data/demo-catalog";
import { buildProduct } from "./build";
import type { Catalog } from "./types";

/** Catálogo de ejemplo para el modo demo (sin Supabase). */
export function getDemoCatalog(): Catalog {
  const categories = demoCategories.map((category) => ({ ...category }));
  const products = demoProducts
    .map((product, index) => {
      const category = categories.find((c) => c.slug === product.categorySlug) ?? null;
      return buildProduct(
        {
          id: product.id,
          slug: product.slug,
          name: product.name,
          description: product.description,
          price: product.price,
          compareAtPrice: product.compareAtPrice ?? null,
          images: demoImages(product.slug),
          featured: Boolean(product.featured),
          createdAt: demoCreatedAt(index),
          category: category && { id: category.id, name: category.name, slug: category.slug },
        },
        product.variants.map((variant, position) => ({
          id: variant.id,
          name: variant.name,
          sku: variant.sku,
          price: variant.price ?? null,
          stock: variant.stock,
          position,
        })),
      );
    })
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  return { categories, products };
}
