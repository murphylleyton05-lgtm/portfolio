import { siteConfig } from "@site-config";
import { parsePostalCode } from "@/lib/argentina";
import type { DeliveryMethod } from "@/lib/supabase/database.types";

export type ShippingQuote = {
  method: DeliveryMethod;
  zoneId: string;
  zoneName: string;
  cost: number;
  eta: string;
  /** true si el envío salió gratis por superar el mínimo. */
  free: boolean;
};

type Zone = { id: string; name: string; cost: number; eta: string };

/** Zona de envío para un CP ("1425" o "C1425ABC"). null si el CP no es válido. */
export function findShippingZone(postalCode: string | undefined): Zone | null {
  const code = postalCode ? parsePostalCode(postalCode) : null;
  if (code === null) return null;
  const zone = siteConfig.shipping.zones.find((z) =>
    z.postalCodeRanges.some(([from, to]) => code >= from && code <= to),
  );
  return zone ?? siteConfig.shipping.defaultZone;
}

/** Métodos de entrega habilitados en site.config.ts. */
export function deliveryMethods(): DeliveryMethod[] {
  const methods: DeliveryMethod[] = [];
  if (siteConfig.shipping.enabled) methods.push("shipping");
  if (siteConfig.pickup.enabled) methods.push("pickup");
  return methods;
}

/**
 * Costo de entrega. Función pura compartida entre el navegador (para mostrar)
 * y el servidor (para cobrar). Devuelve null si el método no está habilitado o
 * falta un CP válido.
 */
export function quoteShipping(input: {
  method: DeliveryMethod;
  postalCode?: string;
  subtotal: number;
}): ShippingQuote | null {
  if (input.method === "pickup") {
    if (!siteConfig.pickup.enabled) return null;
    return {
      method: "pickup",
      zoneId: "pickup",
      zoneName: "Retiro en el local",
      cost: 0,
      eta: siteConfig.pickup.hours,
      free: true,
    };
  }
  if (!siteConfig.shipping.enabled) return null;
  const zone = findShippingZone(input.postalCode);
  if (!zone) return null;
  const threshold = siteConfig.shipping.freeShippingThreshold;
  const free = threshold !== null && input.subtotal >= threshold;
  return { method: "shipping", zoneId: zone.id, zoneName: zone.name, cost: free ? 0 : zone.cost, eta: zone.eta, free };
}
