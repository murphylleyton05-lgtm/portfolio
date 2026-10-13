"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";

/** Oculta el botón flotante donde taparía acciones importantes (carrito y checkout). */
export function HideOnCheckout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  if (pathname.startsWith("/checkout") || pathname.startsWith("/carrito")) return null;
  return children;
}
