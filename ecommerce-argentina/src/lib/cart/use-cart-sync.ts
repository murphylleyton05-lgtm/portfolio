"use client";

import { useEffect, useRef, useState } from "react";
import { refreshCart } from "@/lib/actions/cart";
import { formatPrice } from "@/lib/utils";
import { useCart, useCartHydrated } from "./store";
import { clampQuantity, type CartItem } from "./types";

/**
 * Al abrir carrito/checkout, actualiza precios y stock con el servidor y avisa
 * qué cambió (precio, stock, productos que ya no están).
 */
export function useCartSync() {
  const hydrated = useCartHydrated();
  const hasItems = useCart((state) => state.items.length > 0);
  // null = todavía no respondió el servidor.
  const [notices, setNotices] = useState<string[] | null>(null);
  const started = useRef(false);

  useEffect(() => {
    if (!hydrated || started.current) return;
    started.current = true;
    const items = useCart.getState().items;
    if (!items.length) return;

    refreshCart(items.map(({ variantId, quantity }) => ({ variantId, quantity })))
      .then((result) => {
        if (!result.ok) {
          setNotices([result.error]);
          return;
        }
        const fresh = new Map(result.lines.map((line) => [line.variantId, line]));
        const messages: string[] = [];
        const next: CartItem[] = [];
        for (const item of useCart.getState().items) {
          const line = fresh.get(item.variantId);
          const label = `${item.name} (${item.variantName})`;
          if (!line) {
            messages.push(`${label} ya no está disponible y lo sacamos del carrito.`);
            continue;
          }
          const quantity = clampQuantity(item.quantity, line.stock);
          if (quantity === 0) {
            messages.push(`${label} se quedó sin stock y lo sacamos del carrito.`);
            continue;
          }
          if (quantity < item.quantity) messages.push(`${label}: quedan ${line.stock}, ajustamos la cantidad.`);
          if (line.price !== item.price) messages.push(`${label} ahora cuesta ${formatPrice(line.price)}.`);
          next.push({ ...item, ...line, quantity });
        }
        useCart.getState().replace(next);
        setNotices(messages);
      })
      .catch(() => setNotices(["No pudimos verificar precios y stock. Revisá tu conexión."]));
  }, [hydrated]);

  return { hydrated, syncing: !hydrated || (hasItems && notices === null), notices: notices ?? [] };
}
