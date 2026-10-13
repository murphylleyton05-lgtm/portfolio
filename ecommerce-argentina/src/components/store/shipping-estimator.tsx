"use client";

import { useId, useState } from "react";
import { Truck } from "lucide-react";
import { siteConfig } from "@site-config";
import { quoteShipping } from "@/lib/shipping";
import { formatPrice } from "@/lib/utils";

/** "Calculá tu envío": cotiza por CP con las zonas de site.config.ts. */
export function ShippingEstimator({ subtotal }: { subtotal: number }) {
  const id = useId();
  const [postalCode, setPostalCode] = useState("");
  if (!siteConfig.shipping.enabled) return null;
  const quote = postalCode.length >= 4 ? quoteShipping({ method: "shipping", postalCode, subtotal }) : null;

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-border p-3">
      <label htmlFor={id} className="flex items-center gap-2 text-sm font-medium">
        <Truck className="size-4" aria-hidden /> Calculá tu envío
      </label>
      <input
        id={id}
        value={postalCode}
        onChange={(event) => setPostalCode(event.target.value.slice(0, 8))}
        placeholder="Tu código postal (ej: 1425)"
        inputMode="text"
        autoComplete="postal-code"
        className="h-10 rounded-lg border border-border bg-background px-3 text-sm outline-none focus:border-primary"
      />
      <p className="text-sm text-muted-foreground" aria-live="polite">
        {postalCode.length < 4
          ? siteConfig.shipping.freeShippingThreshold
            ? `Gratis desde ${formatPrice(siteConfig.shipping.freeShippingThreshold)}.`
            : "Ingresá tu código postal."
          : quote
            ? `${quote.zoneName}: ${quote.free ? "¡Gratis!" : formatPrice(quote.cost)} · ${quote.eta}`
            : "Código postal inválido."}
      </p>
    </div>
  );
}
