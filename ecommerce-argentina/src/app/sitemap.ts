import type { MetadataRoute } from "next";
import { getCatalog } from "@/lib/catalog/data";
import { absoluteUrl } from "@/lib/env";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const { categories, products } = await getCatalog();
  return [
    { url: absoluteUrl("/"), changeFrequency: "daily", priority: 1 },
    { url: absoluteUrl("/productos"), changeFrequency: "daily", priority: 0.9 },
    ...categories.map((category) => ({
      url: absoluteUrl(`/productos?categoria=${category.slug}`),
      changeFrequency: "weekly" as const,
      priority: 0.7,
    })),
    ...products.map((product) => ({
      url: absoluteUrl(`/productos/${product.slug}`),
      lastModified: product.createdAt,
      changeFrequency: "weekly" as const,
      priority: 0.8,
    })),
  ];
}
