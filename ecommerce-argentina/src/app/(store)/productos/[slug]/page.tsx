import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { ChevronRight, CreditCard, Store, Truck } from "lucide-react";
import { siteConfig } from "@site-config";
import { AddToCart } from "@/components/store/add-to-cart";
import { ProductGrid } from "@/components/store/product-card";
import { ProductGallery } from "@/components/store/product-gallery";
import { ShippingEstimator } from "@/components/store/shipping-estimator";
import { WhatsAppLink } from "@/components/store/whatsapp-button";
import { Skeleton } from "@/components/ui/skeleton";
import { getCatalog, getProductBySlug, getRelatedProducts } from "@/lib/catalog/data";
import type { CatalogProduct } from "@/lib/catalog/types";
import { absoluteUrl } from "@/lib/env";
import { formatPrice } from "@/lib/utils";

export async function generateStaticParams() {
  const { products } = await getCatalog();
  // Con Cache Components hay que devolver al menos un parámetro.
  return products.length ? products.map((product) => ({ slug: product.slug })) : [{ slug: "sin-productos" }];
}

export async function generateMetadata({ params }: PageProps<"/productos/[slug]">): Promise<Metadata> {
  const { slug } = await params;
  const product = await getProductBySlug(slug);
  if (!product) return { title: "Producto no encontrado", robots: { index: false } };
  const description = product.description.length > 160 ? `${product.description.slice(0, 157)}…` : product.description;
  return {
    title: product.name,
    description,
    alternates: { canonical: `/productos/${product.slug}` },
    openGraph: { title: product.name, description, url: `/productos/${product.slug}` },
  };
}

export default function ProductPage({ params }: PageProps<"/productos/[slug]">) {
  return (
    <div className="container-page py-6 sm:py-10">
      <Suspense fallback={<ProductSkeleton />}>
        <ProductDetail params={params} />
      </Suspense>
    </div>
  );
}

async function ProductDetail({ params }: Pick<PageProps<"/productos/[slug]">, "params">) {
  const { slug } = await params;
  const product = await getProductBySlug(slug);
  if (!product) notFound();
  const related = await getRelatedProducts(product, 4);

  return (
    <>
      <ProductJsonLd product={product} />
      <nav aria-label="Ruta" className="mb-6 flex flex-wrap items-center gap-1 text-sm text-muted-foreground">
        <Link href="/" className="hover:text-foreground">
          Inicio
        </Link>
        <ChevronRight className="size-3.5" aria-hidden />
        <Link href="/productos" className="hover:text-foreground">
          Productos
        </Link>
        {product.category && (
          <>
            <ChevronRight className="size-3.5" aria-hidden />
            <Link href={`/productos?categoria=${product.category.slug}`} className="hover:text-foreground">
              {product.category.name}
            </Link>
          </>
        )}
      </nav>

      <div className="grid gap-8 lg:grid-cols-2 lg:gap-12">
        <ProductGallery images={product.images} name={product.name} />
        <div className="flex flex-col gap-6">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{product.name}</h1>
          <AddToCart product={product} />
          <WhatsAppLink
            message={`¡Hola! Quiero consultar por "${product.name}": ${absoluteUrl(`/productos/${product.slug}`)}`}
          />
          <ShippingEstimator subtotal={product.minPrice} />
          <ul className="flex flex-col gap-3 border-t border-border pt-6 text-sm">
            {siteConfig.shipping.enabled && (
              <li className="flex gap-3">
                <Truck className="size-5 shrink-0 text-muted-foreground" aria-hidden />
                <span>
                  Envíos a todo el país.
                  {siteConfig.shipping.freeShippingThreshold
                    ? ` Gratis desde ${formatPrice(siteConfig.shipping.freeShippingThreshold)}.`
                    : ""}
                </span>
              </li>
            )}
            {siteConfig.pickup.enabled && (
              <li className="flex gap-3">
                <Store className="size-5 shrink-0 text-muted-foreground" aria-hidden />
                <span>
                  Retiro sin cargo en {siteConfig.pickup.address} ({siteConfig.pickup.hours}).
                </span>
              </li>
            )}
            <li className="flex gap-3">
              <CreditCard className="size-5 shrink-0 text-muted-foreground" aria-hidden />
              <span>Pagás seguro con Mercado Pago.</span>
            </li>
          </ul>
          {product.description && (
            <section aria-labelledby="descripcion" className="border-t border-border pt-6">
              <h2 id="descripcion" className="mb-2 font-medium">
                Descripción
              </h2>
              <p className="text-sm leading-relaxed whitespace-pre-line text-muted-foreground">{product.description}</p>
            </section>
          )}
        </div>
      </div>

      {related.length > 0 && (
        <section aria-labelledby="relacionados" className="mt-16">
          <h2 id="relacionados" className="mb-6 text-xl font-semibold tracking-tight">
            También te puede gustar
          </h2>
          <ProductGrid products={related} />
        </section>
      )}
    </>
  );
}

function ProductJsonLd({ product }: { product: CatalogProduct }) {
  const prices = product.variants.map((variant) => variant.price);
  const availability = product.totalStock > 0 ? "https://schema.org/InStock" : "https://schema.org/OutOfStock";
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: product.name,
    description: product.description,
    image: product.images.map((image) => absoluteUrl(image)),
    sku: product.variants[0]?.sku ?? undefined,
    category: product.category?.name,
    brand: { "@type": "Brand", name: siteConfig.name },
    offers:
      new Set(prices).size > 1
        ? {
            "@type": "AggregateOffer",
            priceCurrency: siteConfig.currency,
            lowPrice: Math.min(...prices),
            highPrice: Math.max(...prices),
            offerCount: prices.length,
            availability,
          }
        : {
            "@type": "Offer",
            priceCurrency: siteConfig.currency,
            price: prices[0] ?? product.price,
            availability,
            url: absoluteUrl(`/productos/${product.slug}`),
          },
  };
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }}
    />
  );
}

function ProductSkeleton() {
  return (
    <div role="status" aria-label="Cargando producto" className="grid gap-8 lg:grid-cols-2 lg:gap-12">
      <Skeleton className="aspect-[4/5] rounded-2xl" />
      <div className="flex flex-col gap-4">
        <Skeleton className="h-8 w-3/4" />
        <Skeleton className="h-7 w-32" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    </div>
  );
}
