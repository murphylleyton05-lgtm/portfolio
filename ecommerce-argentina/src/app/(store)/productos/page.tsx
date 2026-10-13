import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { CatalogFilters, SortForm } from "@/components/store/catalog-filters";
import { Pagination } from "@/components/store/pagination";
import { ProductGrid } from "@/components/store/product-card";
import { ProductGridSkeleton } from "@/components/store/product-grid-skeleton";
import { Skeleton } from "@/components/ui/skeleton";
import { getCatalog } from "@/lib/catalog/data";
import { catalogHref, parseCatalogQuery, queryCatalog } from "@/lib/catalog/query";

export async function generateMetadata({ searchParams }: PageProps<"/productos">): Promise<Metadata> {
  const query = parseCatalogQuery(await searchParams);
  const { categories } = await getCatalog();
  const category = categories.find((c) => c.slug === query.categoria);
  const title = query.q ? `Resultados para “${query.q}”` : (category?.name ?? "Productos");
  return {
    title,
    description: category?.description || "Todos los productos de la tienda.",
    alternates: { canonical: category ? `/productos?categoria=${category.slug}` : "/productos" },
    // Las búsquedas y combinaciones de filtros no se indexan.
    robots: query.q || query.min !== undefined || query.max !== undefined || query.stock ? { index: false } : undefined,
  };
}

export default function ProductsPage({ searchParams }: PageProps<"/productos">) {
  return (
    <div className="container-page py-8">
      <Suspense fallback={<ListingSkeleton />}>
        <Listing searchParams={searchParams} />
      </Suspense>
    </div>
  );
}

async function Listing({ searchParams }: Pick<PageProps<"/productos">, "searchParams">) {
  const query = parseCatalogQuery(await searchParams);
  const { categories, products } = await getCatalog();
  const { items, total, page, pageCount } = queryCatalog(products, query);
  const category = categories.find((c) => c.slug === query.categoria);
  const heading = query.q ? `Resultados para “${query.q}”` : (category?.name ?? "Todos los productos");

  return (
    <>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{heading}</h1>
          <p className="text-sm text-muted-foreground" aria-live="polite">
            {total === 1 ? "1 producto" : `${total} productos`}
          </p>
        </div>
        <SortForm query={query} />
      </div>

      <nav aria-label="Categorías" className="-mx-4 mb-6 flex gap-2 overflow-x-auto px-4 pb-1 sm:mx-0 sm:px-0">
        {[{ slug: undefined, name: "Todos" }, ...categories].map((c) => {
          const active = c.slug === query.categoria;
          return (
            <Link
              key={c.slug ?? "todos"}
              href={catalogHref(query, { categoria: c.slug, pagina: 1 })}
              aria-current={active ? "page" : undefined}
              className={
                active
                  ? "rounded-full bg-primary px-4 py-2 text-sm whitespace-nowrap text-primary-foreground"
                  : "rounded-full border border-border px-4 py-2 text-sm whitespace-nowrap hover:border-primary"
              }
            >
              {c.name}
            </Link>
          );
        })}
      </nav>

      <div className="grid gap-8 lg:grid-cols-[15rem_1fr]">
        <aside>
          <CatalogFilters query={query} categories={categories} />
        </aside>
        <section aria-label="Resultados">
          {items.length ? (
            <>
              <ProductGrid products={items} preloadFirst={2} />
              <Pagination query={query} page={page} pageCount={pageCount} />
            </>
          ) : (
            <div className="flex flex-col items-start gap-3 rounded-xl border border-dashed border-border p-8">
              <p className="font-medium">No encontramos productos con esos filtros.</p>
              <Link href="/productos" className="text-sm underline underline-offset-4">
                Ver todos los productos
              </Link>
            </div>
          )}
        </section>
      </div>
    </>
  );
}

function ListingSkeleton() {
  return (
    <>
      <Skeleton className="mb-2 h-8 w-56" />
      <Skeleton className="mb-6 h-4 w-24" />
      <div className="grid gap-8 lg:grid-cols-[15rem_1fr]">
        <Skeleton className="hidden h-80 lg:block" />
        <ProductGridSkeleton />
      </div>
    </>
  );
}
