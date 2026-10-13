import Image from "next/image";
import type { OrderWithItems } from "@/lib/orders/queries";
import { formatPrice } from "@/lib/utils";

/** Items + totales de un pedido (página del cliente y panel admin). */
export function OrderSummary({ order }: { order: OrderWithItems }) {
  return (
    <div className="flex flex-col gap-4">
      <ul className="divide-y divide-border">
        {order.items.map((item) => (
          <li key={item.id} className="flex items-center gap-3 py-3 text-sm">
            <div className="relative aspect-[4/5] w-12 shrink-0 overflow-hidden rounded-md bg-muted">
              {item.image && <Image src={item.image} alt="" fill sizes="48px" className="object-cover" />}
            </div>
            <div className="flex-1">
              <p className="font-medium">{item.product_name}</p>
              <p className="text-muted-foreground">
                {item.variant_name !== "Único" ? `${item.variant_name} · ` : ""}
                {item.quantity} × {formatPrice(item.unit_price)}
                {item.sku ? ` · ${item.sku}` : ""}
              </p>
            </div>
            <p className="tabular-nums">{formatPrice(item.unit_price * item.quantity)}</p>
          </li>
        ))}
      </ul>
      <dl className="flex flex-col gap-1.5 border-t border-border pt-4 text-sm">
        <div className="flex justify-between">
          <dt>Subtotal</dt>
          <dd className="tabular-nums">{formatPrice(order.subtotal)}</dd>
        </div>
        <div className="flex justify-between">
          <dt>{order.delivery_method === "pickup" ? "Retiro" : `Envío${order.shipping_zone ? ` · ${order.shipping_zone}` : ""}`}</dt>
          <dd className="tabular-nums">{order.shipping_cost ? formatPrice(order.shipping_cost) : "Gratis"}</dd>
        </div>
        <div className="flex justify-between text-base font-semibold">
          <dt>Total</dt>
          <dd className="tabular-nums">{formatPrice(order.total)}</dd>
        </div>
      </dl>
    </div>
  );
}
