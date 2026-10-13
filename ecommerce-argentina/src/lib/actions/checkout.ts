"use server";

import { placeOrderSchema } from "@/lib/checkout/schema";
import { createOrder, orderPath } from "@/lib/orders/create";

export type PlaceOrderResult =
  | { ok: true; redirectUrl: string }
  | { ok: false; error: string; problems?: string[]; fieldErrors?: Record<string, string> };

/** Valida el checkout, crea el pedido y devuelve a dónde redirigir al cliente. */
export async function placeOrder(input: unknown): Promise<PlaceOrderResult> {
  const parsed = placeOrderSchema.safeParse(input);
  if (!parsed.success) {
    const fieldErrors: Record<string, string> = {};
    for (const issue of parsed.error.issues) {
      if (issue.path[0] !== "form") continue;
      const key = issue.path.slice(1).join(".");
      fieldErrors[key] ??= issue.message;
    }
    return { ok: false, error: "Revisá los datos marcados.", fieldErrors };
  }

  try {
    const result = await createOrder(parsed.data.form, parsed.data.items);
    if (!result.ok) return result;
    return { ok: true, redirectUrl: orderPath(result.order) };
  } catch (error) {
    console.error("[placeOrder]", error);
    return { ok: false, error: "Ocurrió un error inesperado. Probá de nuevo en unos minutos." };
  }
}

