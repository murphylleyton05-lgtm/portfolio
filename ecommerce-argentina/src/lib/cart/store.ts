"use client";

import { useSyncExternalStore } from "react";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import { clampQuantity, type CartItem } from "./types";

type CartState = {
  items: CartItem[];
  /** Agrega (o suma) una variante. Devuelve la cantidad que efectivamente quedó. */
  add: (item: Omit<CartItem, "quantity">, quantity: number) => number;
  setQuantity: (variantId: string, quantity: number) => void;
  remove: (variantId: string) => void;
  /** Reemplaza el carrito con datos frescos del servidor. */
  replace: (items: CartItem[]) => void;
  clear: () => void;
};

export const useCart = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      add: (item, quantity) => {
        const existing = get().items.find((i) => i.variantId === item.variantId);
        const next = clampQuantity((existing?.quantity ?? 0) + quantity, item.stock);
        set((state) => ({
          items: existing
            ? state.items.map((i) => (i.variantId === item.variantId ? { ...i, ...item, quantity: next } : i))
            : next > 0
              ? [...state.items, { ...item, quantity: next }]
              : state.items,
        }));
        return next;
      },
      setQuantity: (variantId, quantity) =>
        set((state) => ({
          items: state.items
            .map((i) => (i.variantId === variantId ? { ...i, quantity: clampQuantity(quantity, i.stock) } : i))
            .filter((i) => i.quantity > 0),
        })),
      remove: (variantId) => set((state) => ({ items: state.items.filter((i) => i.variantId !== variantId) })),
      replace: (items) => set({ items }),
      clear: () => set({ items: [] }),
    }),
    {
      name: "cart-v1",
      version: 1,
      storage: createJSONStorage(() => localStorage),
      // Se rehidrata en <CartHydrator /> después de montar, para no generar
      // diferencias entre el HTML del servidor (carrito vacío) y el cliente.
      skipHydration: true,
      partialize: (state) => ({ items: state.items }),
    },
  ),
);

const subscribeHydration = (callback: () => void) => useCart.persist.onFinishHydration(callback);
const getHydrated = () => useCart.persist.hasHydrated();
const getServerHydrated = () => false;

/** true cuando el carrito ya se leyó de localStorage. */
export function useCartHydrated() {
  return useSyncExternalStore(subscribeHydration, getHydrated, getServerHydrated);
}
