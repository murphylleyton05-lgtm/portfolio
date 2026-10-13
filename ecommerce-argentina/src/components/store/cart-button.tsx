"use client";

import Link from "next/link";
import { ShoppingBag } from "lucide-react";
import { useCart, useCartHydrated } from "@/lib/cart/store";
import { cartCount } from "@/lib/cart/types";

export function CartButton() {
  const hydrated = useCartHydrated();
  const count = useCart((state) => cartCount(state.items));
  const visibleCount = hydrated ? count : 0;

  return (
    <Link
      href="/carrito"
      className="relative inline-flex size-10 items-center justify-center rounded-lg hover:bg-muted"
      aria-label={visibleCount ? `Carrito, ${visibleCount} productos` : "Carrito"}
    >
      <ShoppingBag className="size-5" aria-hidden />
      {visibleCount > 0 && (
        <span className="absolute -top-0.5 -right-0.5 flex min-w-5 items-center justify-center rounded-full bg-accent px-1 text-[11px] leading-5 font-semibold text-accent-foreground tabular-nums">
          {visibleCount > 99 ? "99+" : visibleCount}
        </span>
      )}
    </Link>
  );
}
