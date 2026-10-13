"use server";

import { revalidatePath, updateTag } from "next/cache";
import { requireAdminAction } from "@/lib/admin/auth";
import { orderStatusSchema } from "@/lib/admin/schemas";
import { CATALOG_TAG } from "@/lib/catalog/data";
import { ORDER_STATUS_LABEL } from "@/lib/orders/status";

export type OrderStatusState = { ok?: boolean; error?: string; message?: string };

export async function updateOrderStatus(_prev: OrderStatusState, formData: FormData): Promise<OrderStatusState> {
  const { supabase } = await requireAdminAction();
  const parsed = orderStatusSchema.safeParse({ orderId: formData.get("orderId"), status: formData.get("status") });
  if (!parsed.success) return { error: "Estado inválido." };

  const { error } = await supabase.rpc("set_order_status", {
    p_order_id: parsed.data.orderId,
    p_status: parsed.data.status,
  });
  if (error) {
    console.error("[updateOrderStatus]", error);
    return { error: "No se pudo cambiar el estado." };
  }

  // Cambiar el estado puede descontar o reponer stock.
  updateTag(CATALOG_TAG);
  revalidatePath(`/admin/pedidos/${parsed.data.orderId}`);
  revalidatePath("/admin/pedidos");
  return { ok: true, message: `Estado actualizado a "${ORDER_STATUS_LABEL[parsed.data.status]}".` };
}
