"use client";

import { useEffect, useId, useState } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { siteConfig } from "@site-config";

type NavLink = { href: string; label: string };

export function MobileMenu({ links }: { links: NavLink[] }) {
  const [open, setOpen] = useState(false);
  const panelId = useId();

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <div className="md:hidden">
      <button
        type="button"
        className="inline-flex size-10 items-center justify-center rounded-lg hover:bg-muted"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label="Abrir menú"
        onClick={() => setOpen(true)}
      >
        <Menu className="size-5" aria-hidden />
      </button>
      {open && (
        <div id={panelId} role="dialog" aria-modal="true" aria-label="Menú" className="fixed inset-0 z-[60] flex flex-col bg-background">
          <div className="container-page flex h-16 shrink-0 items-center justify-between border-b border-border">
            <span className="font-semibold">{siteConfig.name}</span>
            <button
              type="button"
              className="inline-flex size-10 items-center justify-center rounded-lg hover:bg-muted"
              aria-label="Cerrar menú"
              onClick={() => setOpen(false)}
              autoFocus
            >
              <X className="size-5" aria-hidden />
            </button>
          </div>
          <nav aria-label="Menú principal" className="container-page flex flex-1 flex-col overflow-y-auto py-2">
            {links.map((link) => (
              <Link key={link.href} href={link.href} onClick={() => setOpen(false)} className="border-b border-border py-4 text-lg font-medium">
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
      )}
    </div>
  );
}
