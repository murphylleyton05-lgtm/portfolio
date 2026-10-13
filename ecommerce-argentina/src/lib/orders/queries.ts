import "server-only";
import { createServiceClient } from "@/lib/supabase/admin";
import type { Tables } from "@/lib/supabase/database.types";
import type { ShippingAddress } from "@/lib/checkout/schema";

export type OrderWithItems = Tables<"orders"> & { items: Tables<"order_items">[] };

/** Pedido visto por el cliente: requiere id + token secreto. */
export async function getOrderForCustomer(id: string, token: string): Promise<OrderWithItems | null> {
  const supabase = createServiceClient();
  const { data, error } = await supabase
    .from("orders")
    .select("*, items:order_items(*)")
    .eq("id", id)
    .eq("access_token", token)
    // Con signal propio Next no deduplica el GET: después de confirmar un pago
    // en el mismo render, la segunda lectura trae el estado actualizado.
    .abortSignal(AbortSignal.timeout(10_000))
    .maybeSingle();
  if (error) throw new Error(`No se pudo leer el pedido: ${error.message}`);
  return data;
}

export function shippingAddressOf(order: Pick<Tables<"orders">, "shipping_address">): ShippingAddress | null {
  return (order.shipping_address as ShippingAddress | null) ?? null;
}

export function formatAddress(address: ShippingAddress) {
  const line1 = [address.street, address.number, address.apartment].filter(Boolean).join(" ");
  return `${line1}, ${address.city} (${address.postalCode}), ${address.province}`;
}
