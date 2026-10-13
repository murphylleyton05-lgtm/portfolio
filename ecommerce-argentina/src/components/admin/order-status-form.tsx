"use client";

import { useActionState } from "react";
import { updateOrderStatus, type OrderStatusState } from "@/lib/actions/admin/orders";
import { ORDER_STATUSES, ORDER_STATUS_LABEL } from "@/lib/orders/status";
import type { OrderStatus } from "@/lib/supabase/database.types";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/field";

export function OrderStatusForm({ orderId, status }: { orderId: string; status: OrderStatus }) {
  const [state, action, pending] = useActionState<OrderStatusState, FormData>(updateOrderStatus, {});
  return (
    <form action={action} className="flex flex-col gap-3">
      <input type="hidden" name="orderId" value={orderId} />
      <label htmlFor="status" className="text-sm font-medium">
        Cambiar estado
      </label>
      <div className="flex gap-2">
        <Select id="status" name="status" defaultValue={status} key={status}>
          {ORDER_STATUSES.map((value) => (
            <option key={value} value={value}>
              {ORDER_STATUS_LABEL[value]}
            </option>
          ))}
        </Select>
        <Button type="submit" loading={pending}>
          Guardar
        </Button>
      </div>
      <p className="text-xs text-muted-foreground">
        Cancelar (o volver a &quot;pendiente&quot;) repone el stock. Marcar como pagado/preparando/enviado lo descuenta
        si todavía no se había descontado.
      </p>
      {state.error && <Alert tone="error">{state.error}</Alert>}
      {state.ok && state.message && <Alert tone="success">{state.message}</Alert>}
    </form>
  );
}
