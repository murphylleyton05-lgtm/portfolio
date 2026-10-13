import Link from "next/link";
import { ArrowRight, CreditCard, Store, Truck } from "lucide-react";
import { siteConfig } from "@site-config";
import { buttonClasses } from "@/components/ui/button";
import { ProductGrid } from "@/components/store/product-card";
import { getCatalog, getFeaturedProducts } from "@/lib/catalog/data";
import { formatPrice } from "@/lib/utils";

export default async function HomePage() {
  const [featured, { categories, products }] = await Promise.all([getFeaturedProducts(8), getCatalog()]);
  const benefits = [
    siteConfig.shipping.enabled && {
      Icon: Truck,
      title: "Envíos a todo el país",
      text: siteConfig.shipping.freeShippingThreshold
        ? `Gratis en compras desde ${formatPrice(siteConfig.shipping.freeShippingThreshold)}.`
        : "Calculá el costo con tu código postal.",
    },
    {
      Icon: CreditCard,
      title: "Pagá como quieras",
      text: siteConfig.payments.installmentsBanner || "Tarjetas, transferencia o efectivo con Mercado Pago.",
    },
    siteConfig.pickup.enabled && { Icon: Store, title: "Retiro sin cargo", text: siteConfig.pickup.address },
  ].filter(Boolean) as Array<{ Icon: typeof Truck; title: string; text: string }>;

  return (
    <>
      <section className="border-b border-border bg-muted/50">
        <div className="container-page flex flex-col items-start gap-6 py-16 sm:py-24">
          <p className="text-sm font-medium text-accent">{siteConfig.name}</p>
          <h1 className="max-w-2xl text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
            {siteConfig.tagline}
          </h1>
          <p className="max-w-xl text-muted-foreground">{siteConfig.description}</p>
          <div className="flex flex-wrap gap-3">
            <Link href="/productos" className={buttonClasses("primary", "lg")}>
              Ver productos <ArrowRight className="size-4" aria-hidden />
            </Link>
            {categories[0] && (
              <Link href={`/productos?categoria=${categories[0].slug}`} className={buttonClasses("outline", "lg")}>
                {categories[0].name}
              </Link>
            )}
          </div>
        </div>
      </section>

      <section aria-labelledby="destacados" className="container-page py-12">
        <div className="mb-6 flex items-end justify-between gap-4">
          <h2 id="destacados" className="text-2xl font-semibold tracking-tight">
            Destacados
          </h2>
          <Link href="/productos" className="text-sm font-medium underline-offset-4 hover:underline">
            Ver todo ({products.length})
          </Link>
        </div>
        {featured.length ? (
          <ProductGrid products={featured} preloadFirst={2} />
        ) : (
          <p className="text-muted-foreground">Todavía no hay productos cargados.</p>
        )}
      </section>

      {categories.length > 0 && (
        <section aria-labelledby="categorias" className="container-page py-6">
          <h2 id="categorias" className="mb-6 text-2xl font-semibold tracking-tight">
            Categorías
          </h2>
          <ul className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {categories.map((category) => (
              <li key={category.id}>
                <Link
                  href={`/productos?categoria=${category.slug}`}
                  className="flex h-full flex-col justify-between gap-6 rounded-xl border border-border p-5 transition hover:border-primary"
                >
                  <span className="font-medium">{category.name}</span>
                  {category.description && (
                    <span className="text-sm text-muted-foreground">{category.description}</span>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section aria-label="Beneficios" className="container-page py-12">
        <ul className="grid gap-6 rounded-2xl bg-muted/60 p-6 sm:grid-cols-3 sm:p-8">
          {benefits.map(({ Icon, title, text }) => (
            <li key={title} className="flex gap-4">
              <Icon className="size-6 shrink-0 text-accent" aria-hidden />
              <div>
                <p className="font-medium">{title}</p>
                <p className="text-sm text-muted-foreground">{text}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
