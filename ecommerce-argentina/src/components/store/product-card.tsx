import Image from "next/image";
import Link from "next/link";
import { siteConfig } from "@site-config";
import { Badge } from "@/components/ui/badge";
import type { CatalogProduct } from "@/lib/catalog/types";
import { Price, discountPercent } from "./price";

export function ProductCard({ product, preload = false }: { product: CatalogProduct; preload?: boolean }) {
  const discount = discountPercent(product.price, product.compareAtPrice);
  const soldOut = product.totalStock <= 0;
  const lowStock = !soldOut && product.totalStock <= siteConfig.catalog.lowStockThreshold;
  const image = product.images[0];

  return (
    <Link href={`/productos/${product.slug}`} className="group flex flex-col gap-3">
      <div className="relative aspect-[4/5] overflow-hidden rounded-xl bg-muted">
        {image ? (
          <Image
            src={image}
            alt={product.name}
            fill
            preload={preload}
            sizes="(min-width: 1024px) 25vw, (min-width: 640px) 33vw, 50vw"
            className="object-cover transition duration-500 group-hover:scale-[1.03]"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-muted-foreground">Sin imagen</div>
        )}
        <div className="absolute top-2 left-2 flex flex-col items-start gap-1">
          {soldOut ? (
            <Badge tone="dark">Sin stock</Badge>
          ) : discount > 0 ? (
            <Badge tone="accent">-{discount}%</Badge>
          ) : null}
          {lowStock && <Badge tone="warning">Últimas unidades</Badge>}
        </div>
      </div>
      <div className="flex flex-col gap-1">
        <h3 className="text-sm leading-snug font-medium group-hover:underline">{product.name}</h3>
        <Price
          amount={product.minPrice}
          compareAt={product.hasPriceRange ? null : product.compareAtPrice}
          from={product.hasPriceRange}
          size="sm"
        />
      </div>
    </Link>
  );
}

export function ProductGrid({ products, preloadFirst = 0 }: { products: CatalogProduct[]; preloadFirst?: number }) {
  return (
    <ul className="grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 lg:grid-cols-4">
      {products.map((product, index) => (
        <li key={product.id}>
          <ProductCard product={product} preload={index < preloadFirst} />
        </li>
      ))}
    </ul>
  );
}
