import Link from "next/link";
import { siteConfig } from "@site-config";
import { getCatalog } from "@/lib/catalog/data";
import { formatPrice } from "@/lib/utils";
import { CartButton } from "./cart-button";
import { Logo } from "./logo";
import { MobileMenu } from "./mobile-menu";
import { SearchForm } from "./search-form";

export async function SiteHeader() {
  const { categories } = await getCatalog();
  const links = [
    { href: "/productos", label: "Todos los productos" },
    ...categories.map((category) => ({ href: `/productos?categoria=${category.slug}`, label: category.name })),
  ];
  const announcements = [
    siteConfig.shipping.enabled && siteConfig.shipping.freeShippingThreshold
      ? `Envío gratis desde ${formatPrice(siteConfig.shipping.freeShippingThreshold)}`
      : null,
    siteConfig.payments.installmentsBanner || null,
    siteConfig.pickup.enabled ? "Retiro sin cargo" : null,
  ].filter(Boolean);

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur">
      {announcements.length > 0 && (
        <p className="bg-primary px-4 py-1.5 text-center text-xs text-primary-foreground">{announcements.join(" · ")}</p>
      )}
      <div className="container-page flex h-16 items-center gap-2 md:gap-6">
        <MobileMenu links={links} />
        <Logo />
        <nav aria-label="Categorías" className="hidden flex-1 items-center gap-5 text-sm md:flex">
          {links.map((link) => (
            <Link key={link.href} href={link.href} className="text-muted-foreground transition hover:text-foreground">
              {link.label === "Todos los productos" ? "Productos" : link.label}
            </Link>
          ))}
        </nav>
        <SearchForm id="search-desktop" className="ml-auto hidden w-64 lg:block" />
        <div className="ml-auto lg:ml-0">
          <CartButton />
        </div>
      </div>
      <div className="container-page pb-3 lg:hidden">
        <SearchForm id="search-mobile" />
      </div>
    </header>
  );
}
