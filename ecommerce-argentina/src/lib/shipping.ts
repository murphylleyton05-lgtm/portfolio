import { siteConfig } from "@site-config";
import type { DeliveryMethod } from "@/lib/supabase/database.types";

export type ShippingQuote = {
  method: DeliveryMethod;
  zoneId: string;
  zoneName: string;
  cost: number;
  eta: string;
};

/**
 * Costo de envío. Por ahora tarifa única (`defaultZone` de site.config.ts).
 * Pura y compartida entre cliente (para mostrar) y servidor (para cobrar).
 */
export function quoteShipping(input: { method: DeliveryMethod; postalCode?: string; subtotal: number }): ShippingQuote {
  const zone = siteConfig.shipping.defaultZone;
  return { method: input.method, zoneId: zone.id, zoneName: zone.name, cost: zone.cost, eta: zone.eta };
}
