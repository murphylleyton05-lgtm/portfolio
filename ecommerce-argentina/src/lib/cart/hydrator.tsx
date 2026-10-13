"use client";

import { useEffect } from "react";
import { useCart } from "./store";

/** Lee el carrito guardado y lo mantiene sincronizado entre pestañas. */
export function CartHydrator() {
  useEffect(() => {
    void useCart.persist.rehydrate();
    const onStorage = (event: StorageEvent) => {
      if (event.key === useCart.persist.getOptions().name) void useCart.persist.rehydrate();
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);
  return null;
}
