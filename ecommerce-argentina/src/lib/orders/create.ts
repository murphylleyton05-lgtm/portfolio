import "server-only";
import { getLiveVariants, type LiveVariant } from "@/lib/catalog/live";
import type { CheckoutFormValues } from "@/lib/checkout/schema";
import { canCreateOrders } from "@/lib/env.server";
import { quoteShipping } from "@/lib/shipping";
import { createServiceClient } from "@/lib/supabase/admin";
import type { Json } from "@/lib/supabase/database.types";
import { roundMoney } from "@/lib/utils";

export type CreatedOrder = {
  id: string;
  number: number;
  accessToken: string;
  total: number;
  lines: Array<LiveVariant & { quantity: number }>;
  shippingCost: number;
  form: CheckoutFormValues;
};

export type CreateOrderResult = { ok: true; order: CreatedOrder } | { ok: false; error: string; problems?: string[] };

/**
 * Crea el pedido con precios y stock leídos del servidor (nunca del navegador).
 * El stock se valida acá pero se descuenta recién cuando se aprueba el pago.
 */
export async function createOrder(
  form: CheckoutFormValues,
  items: Array<{ variantId: string; quantity: number }>,
): Promise<CreateOrderResult> {
  if (!canCreateOrders) {
    return {
      ok: false,
      error: "La tienda está en modo demo: configurá Supabase para recibir pedidos (ver README).",
    };
  }

  // Unificar líneas repetidas de la misma variante.
  const quantities = new Map<string, number>();
  for (const item of items) quantities.set(item.variantId, (quantities.get(item.variantId) ?? 0) + item.quantity);

  const live = await getLiveVariants([...quantities.keys()]);
  const problems: string[] = [];
  const lines: CreatedOrder["lines"] = [];
  for (const [variantId, quantity] of quantities) {
    const variant = live.get(variantId);
    if (!variant) {
      problems.push("Un producto de tu carrito ya no está disponible.");
    } else if (variant.stock < quantity) {
      const label = `${variant.name} (${variant.variantName})`;
      problems.push(variant.stock > 0 ? `${label}: quedan ${variant.stock}.` : `${label}: sin stock.`);
    } else {
      lines.push({ ...variant, quantity });
    }
  }
  if (problems.length) {
    return { ok: false, error: "Hay cambios de stock en tu carrito. Revisalo antes de seguir.", problems };
  }

  const subtotal = roundMoney(lines.reduce((sum, line) => sum + line.price * line.quantity, 0));
  const shipping = quoteShipping({
    method: form.deliveryMethod,
    postalCode: form.deliveryMethod === "shipping" ? form.address.postalCode : undefined,
    subtotal,
  });
  if (!shipping) {
    return { ok: false, error: "El método de entrega elegido no está disponible. Revisá el código postal." };
  }
  const total = roundMoney(subtotal + shipping.cost);

  const supabase = createServiceClient();

  const { data: customer, error: customerError } = await supabase
    .from("customers")
    .upsert({ email: form.email, name: form.name, phone: form.phone, dni: form.dni ?? null }, { onConflict: "email" })
    .select("id")
    .single();
  if (customerError) {
    console.error("[createOrder] customer", customerError);
    return { ok: false, error: "No pudimos registrar tus datos. Probá de nuevo en unos minutos." };
  }

  const { data: order, error: orderError } = await supabase
    .from("orders")
    .insert({
      customer_id: customer.id,
      customer_name: form.name,
      customer_email: form.email,
      customer_phone: form.phone,
      customer_dni: form.dni ?? null,
      delivery_method: form.deliveryMethod,
      shipping_address: form.deliveryMethod === "shipping" ? (form.address as unknown as Json) : null,
      shipping_zone: shipping.zoneName,
      subtotal,
      shipping_cost: shipping.cost,
      total,
      notes: form.notes ?? null,
    })
    .select("id, number, access_token")
    .single();
  if (orderError) {
    console.error("[createOrder] order", orderError);
    return { ok: false, error: "No pudimos crear el pedido. Probá de nuevo en unos minutos." };
  }

  const { error: itemsError } = await supabase.from("order_items").insert(
    lines.map((line) => ({
      order_id: order.id,
      product_id: line.productId,
      variant_id: line.variantId,
      product_name: line.name,
      variant_name: line.variantName,
      sku: line.sku,
      image: line.image,
      unit_price: line.price,
      quantity: line.quantity,
    })),
  );
  if (itemsError) {
    console.error("[createOrder] items", itemsError);
    await supabase.from("orders").delete().eq("id", order.id);
    return { ok: false, error: "No pudimos crear el pedido. Probá de nuevo en unos minutos." };
  }

  return {
    ok: true,
    order: {
      id: order.id,
      number: order.number,
      accessToken: order.access_token,
      total,
      lines,
      shippingCost: shipping.cost,
      form,
    },
  };
}

export function orderPath(order: { id: string; accessToken: string }) {
  return `/pedido/${order.id}?token=${order.accessToken}`;
}
