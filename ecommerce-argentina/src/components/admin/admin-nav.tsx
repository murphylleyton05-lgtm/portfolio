"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Boxes, ClipboardList, ExternalLink, LayoutDashboard, Package, Tag } from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { href: "/admin", label: "Inicio", Icon: LayoutDashboard },
  { href: "/admin/pedidos", label: "Pedidos", Icon: ClipboardList },
  { href: "/admin/productos", label: "Productos", Icon: Package },
  { href: "/admin/stock", label: "Stock", Icon: Boxes },
  { href: "/admin/categorias", label: "Categorías", Icon: Tag },
];

export function AdminNav() {
  const pathname = usePathname();
  return (
    <nav aria-label="Panel" className="flex gap-1 overflow-x-auto md:flex-col">
      {links.map(({ href, label, Icon }) => {
        const active = href === "/admin" ? pathname === "/admin" : pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex items-center gap-2 rounded-lg px-3 py-2 text-sm whitespace-nowrap transition",
              active
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
          >
            <Icon className="size-4" aria-hidden />
            {label}
          </Link>
        );
      })}
      <Link
        href="/"
        target="_blank"
        className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm whitespace-nowrap text-muted-foreground hover:bg-muted hover:text-foreground md:mt-4"
      >
        <ExternalLink className="size-4" aria-hidden />
        Ver tienda
      </Link>
    </nav>
  );
}
