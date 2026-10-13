import "server-only";
import { isMercadoPagoConfigured } from "@/lib/env.server";
import { syncPayment, syncPaymentsForOrder, type SyncResult } from "@/lib/payments/mercadopago";
import type { OrderWithItems } from "./queries";

/**
 * Al volver de Mercado Pago confirmamos el pago sin esperar al webhook (que en
 * local ni siquiera llega). Usa el payment_id de la URL o busca los pagos del
 * pedido. Nunca confía en el "status" de la URL: siempre consulta la API.
 */
export async function syncPendingOrder(
  order: Pick<OrderWithItems, "id" | "status" | "mp_preference_id">,
  paymentIdFromUrl: string | undefined,
): Promise<SyncResult | null> {
  if (!isMercadoPagoConfigured || order.status !== "pending_payment") return null;
  try {
    if (paymentIdFromUrl && /^\d{1,30}$/.test(paymentIdFromUrl)) {
      const result = await syncPayment(paymentIdFromUrl);
      // Solo vale si el pago es de ESTE pedido.
      if (result?.orderId === order.id) return result;
    }
    if (order.mp_preference_id) return await syncPaymentsForOrder(order.id);
  } catch (error) {
    console.error("[syncPendingOrder]", error);
  }
  return null;
}
