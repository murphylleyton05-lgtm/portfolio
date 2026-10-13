"use server";

import { redirect } from "next/navigation";
import { z } from "zod";
import { placeOrderSchema } from "@/lib/checkout/schema";
import { isMercadoPagoConfigured } from "@/lib/env.server";
import { createOrder, orderPath } from "@/lib/orders/create";
import { getOrderForCustomer } from "@/lib/orders/queries";
import { createPreference, preferenceInputFromOrder, preferenceInputFromStoredOrder } from "@/lib/payments/mercadopago";

export type PlaceOrderResult =
  | { ok: true; redirectUrl: string }
  | { ok: false; error: string; problems?: string[]; fieldErrors?: Record<string, string> };

/**
 * Valida el checkout, crea el pedido y devuelve a dónde mandar al cliente:
 * al Checkout Pro de Mercado Pago o, si no está configurado o falla, a la
 * página del pedido (desde ahí puede reintentar el pago).
 */
export async function placeOrder(input: unknown): Promise<PlaceOrderResult> {
  const parsed = placeOrderSchema.safeParse(input);
  if (!parsed.success) {
    const fieldErrors: Record<string, string> = {};
    for (const issue of parsed.error.issues) {
      if (issue.path[0] !== "form") continue;
      fieldErrors[issue.path.slice(1).join(".")] ??= issue.message;
    }
    return { ok: false, error: "Revisá los datos marcados.", fieldErrors };
  }

  let result;
  try {
    result = await createOrder(parsed.data.form, parsed.data.items);
  } catch (error) {
    console.error("[placeOrder]", error);
    return { ok: false, error: "Ocurrió un error inesperado. Probá de nuevo en unos minutos." };
  }
  if (!result.ok) return result;

  if (isMercadoPagoConfigured) {
    try {
      const preference = await createPreference(preferenceInputFromOrder(result.order));
      return { ok: true, redirectUrl: preference.initPoint };
    } catch (error) {
      // El pedido ya existe: lo mandamos a su página para reintentar el pago.
      console.error("[placeOrder] Mercado Pago", error);
    }
  }
  return { ok: true, redirectUrl: orderPath(result.order) };
}

const startPaymentSchema = z.object({ orderId: z.uuid(), token: z.uuid() });

/** Botón "Pagar" de la página del pedido cuando no hay link de pago guardado. */
export async function startPayment(formData: FormData): Promise<void> {
  const parsed = startPaymentSchema.safeParse({ orderId: formData.get("orderId"), token: formData.get("token") });
  if (!parsed.success || !isMercadoPagoConfigured) return;
  const order = await getOrderForCustomer(parsed.data.orderId, parsed.data.token);
  if (!order || order.status !== "pending_payment") return;
  const preference = await createPreference(preferenceInputFromStoredOrder(order));
  redirect(preference.initPoint);
}
