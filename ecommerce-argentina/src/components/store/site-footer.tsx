import Link from "next/link";
import { CreditCard, Mail, MapPin, Phone, Store, Truck } from "lucide-react";
import { siteConfig } from "@site-config";
import { getCatalog } from "@/lib/catalog/data";
import { whatsappUrl } from "@/lib/utils";
import { FacebookIcon, InstagramIcon, TikTokIcon, WhatsAppIcon, XIcon } from "./brand-icons";

const socialLinks = [
  { href: siteConfig.social.instagram, label: "Instagram", Icon: InstagramIcon },
  { href: siteConfig.social.facebook, label: "Facebook", Icon: FacebookIcon },
  { href: siteConfig.social.tiktok, label: "TikTok", Icon: TikTokIcon },
  { href: siteConfig.social.x, label: "X", Icon: XIcon },
].filter((link) => link.href);

export async function SiteFooter() {
  const { categories } = await getCatalog();

  return (
    <footer className="mt-16 border-t border-border bg-muted/40">
      <div className="container-page grid gap-10 py-12 sm:grid-cols-2 lg:grid-cols-4">
        <div className="flex flex-col gap-3">
          <p className="text-lg font-semibold">{siteConfig.name}</p>
          <p className="text-sm text-muted-foreground">{siteConfig.description}</p>
          {socialLinks.length > 0 && (
            <ul className="flex gap-2">
              {socialLinks.map(({ href, label, Icon }) => (
                <li key={label}>
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={label}
                    className="inline-flex size-9 items-center justify-center rounded-full border border-border hover:bg-background"
                  >
                    <Icon width={16} height={16} />
                  </a>
                </li>
              ))}
            </ul>
          )}
        </div>

        <nav aria-label="Catálogo" className="flex flex-col gap-2 text-sm">
          <p className="font-medium">Catálogo</p>
          <Link href="/productos" className="text-muted-foreground hover:text-foreground">
            Todos los productos
          </Link>
          {categories.map((category) => (
            <Link key={category.id} href={`/productos?categoria=${category.slug}`} className="text-muted-foreground hover:text-foreground">
              {category.name}
            </Link>
          ))}
        </nav>

        <div className="flex flex-col gap-2 text-sm">
          <p className="font-medium">Compras</p>
          <p className="flex items-start gap-2 text-muted-foreground">
            <CreditCard className="mt-0.5 size-4 shrink-0" aria-hidden />
            Pagás con Mercado Pago: tarjetas, transferencia o efectivo.
          </p>
          {siteConfig.shipping.enabled && (
            <p className="flex items-start gap-2 text-muted-foreground">
              <Truck className="mt-0.5 size-4 shrink-0" aria-hidden />
              Envíos a todo el país.
            </p>
          )}
          {siteConfig.pickup.enabled && (
            <p className="flex items-start gap-2 text-muted-foreground">
              <Store className="mt-0.5 size-4 shrink-0" aria-hidden />
              Retiro: {siteConfig.pickup.address} · {siteConfig.pickup.hours}
            </p>
          )}
        </div>

        <div className="flex flex-col gap-2 text-sm">
          <p className="font-medium">Contacto</p>
          <a
            href={whatsappUrl(siteConfig.contact.whatsappDefaultMessage)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground"
          >
            <WhatsAppIcon width={16} height={16} /> WhatsApp
          </a>
          <a href={`mailto:${siteConfig.contact.email}`} className="flex items-center gap-2 text-muted-foreground hover:text-foreground">
            <Mail className="size-4" aria-hidden /> {siteConfig.contact.email}
          </a>
          <a
            href={`tel:${siteConfig.contact.phone.replace(/[^\d+]/g, "")}`}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground"
          >
            <Phone className="size-4" aria-hidden /> {siteConfig.contact.phone}
          </a>
          <p className="flex items-center gap-2 text-muted-foreground">
            <MapPin className="size-4" aria-hidden /> {siteConfig.contact.address}
          </p>
        </div>
      </div>
      <p className="border-t border-border py-6 text-center text-xs text-muted-foreground">
        © {siteConfig.name} · Precios en pesos argentinos con IVA incluido.
      </p>
    </footer>
  );
}
