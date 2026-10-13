import type { BadgeTone } from "@/components/ui/badge";
import type { OrderStatus } from "@/lib/supabase/database.types";

export const ORDER_STATUSES: OrderStatus[] = [
  "pending_payment",
  "paid",
  "preparing",
  "shipped",
  "ready_for_pickup",
  "delivered",
  "cancelled",
];

export const ORDER_STATUS_LABEL: Record<OrderStatus, string> = {
  pending_payment: "Pendiente de pago",
  paid: "Pagado",
  preparing: "En preparación",
  shipped: "Enviado",
  ready_for_pickup: "Listo para retirar",
  delivered: "Entregado",
  cancelled: "Cancelado",
};

export const ORDER_STATUS_TONE: Record<OrderStatus, BadgeTone> = {
  pending_payment: "warning",
  paid: "success",
  preparing: "info",
  shipped: "info",
  ready_for_pickup: "info",
  delivered: "neutral",
  cancelled: "danger",
};

/** Mensaje para el cliente en la página de su pedido. */
export const ORDER_STATUS_MESSAGE: Record<OrderStatus, string> = {
  pending_payment: "Tu pedido está reservado y espera el pago.",
  paid: "¡Gracias! Recibimos tu pago y ya estamos preparando tu pedido.",
  preparing: "Estamos preparando tu pedido.",
  shipped: "Tu pedido está en camino.",
  ready_for_pickup: "Tu pedido está listo para retirar.",
  delivered: "Tu pedido fue entregado. ¡Gracias por tu compra!",
  cancelled: "Este pedido fue cancelado. Si tenés dudas, escribinos.",
};
