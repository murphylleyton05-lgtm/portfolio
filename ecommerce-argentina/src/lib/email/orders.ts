import "server-only";
import { siteConfig } from "@site-config";
import { absoluteUrl } from "@/lib/env";
import { canCreateOrders } from "@/lib/env.server";
import { createServiceClient } from "@/lib/supabase/admin";
import { orderPath } from "@/lib/orders/create";
import type { OrderWithItems } from "@/lib/orders/queries";
import type { OrderStatus } from "@/lib/supabase/database.types";
import { sendEmail } from "./send";
import { newOrderNotificationEmail, orderConfirmationEmail, orderStatusEmail } from "./templates";

const PAID_STATUSES: OrderStatus[] = ["paid", "preparing", "shipped", "ready_for_pickup", "delivered"];

async function loadOrder(orderId: string): Promise<OrderWithItems | null> {
  const { data, error } = await createServiceClient()
    .from("orders")
    .select("*, items:order_items(*)")
    .eq("id", orderId)
    .maybeSingle();
  if (error) throw new Error(`No se pudo leer el pedido ${orderId}: ${error.message}`);
  return data;
}

const customerOrderUrl = (order: OrderWithItems) => absoluteUrl(orderPath({ id: order.id, accessToken: order.access_token }));

/**
 * Email de confirmación al cliente + aviso a la tienda. Se manda UNA sola vez
 * por pedido (se "reserva" con confirmation_email_sent_at). Si el envío al
 * cliente falla se libera la reserva para reintentar en la próxima
 * notificación del pago.
 */
export async function sendOrderEmails(orderId: string) {
  if (!canCreateOrders) return;
  try {
    const supabase = createServiceClient();
    const { data: claimed, error } = await supabase
      .from("orders")
      .update({ confirmation_email_sent_at: new Date().toISOString() })
      .eq("id", orderId)
      .is("confirmation_email_sent_at", null)
      .in("status", PAID_STATUSES)
      .select("id");
    if (error) throw error;
    if (!claimed.length) return; // ya se mandó (o el pedido no está pago)

    const order = await loadOrder(orderId);
    if (!order) return;

    const confirmation = orderConfirmationEmail(order, customerOrderUrl(order));
    const sent = await sendEmail({ to: order.customer_email, ...confirmation, idempotencyKey: `order-confirmation/${order.id}` });
    if (!sent.ok) {
      await supabase.from("orders").update({ confirmation_email_sent_at: null }).eq("id", orderId);
      return;
    }

    if (siteConfig.contact.email) {
      const notification = newOrderNotificationEmail(order, absoluteUrl(`/admin/pedidos/${order.id}`));
      await sendEmail({ to: siteConfig.contact.email, ...notification, idempotencyKey: `order-notification/${order.id}` });
    }
  } catch (error) {
    console.error("[sendOrderEmails]", error);
  }
}

/** Avisa al cliente cuando el admin marca "enviado" o "listo para retirar". */
export async function sendOrderStatusEmail(orderId: string) {
  if (!canCreateOrders) return;
  try {
    const order = await loadOrder(orderId);
    if (!order || (order.status !== "shipped" && order.status !== "ready_for_pickup")) return;
    await sendEmail({
      to: order.customer_email,
      ...orderStatusEmail(order, customerOrderUrl(order)),
      idempotencyKey: `order-status/${order.id}/${order.status}`,
    });
  } catch (error) {
    console.error("[sendOrderStatusEmail]", error);
  }
}
