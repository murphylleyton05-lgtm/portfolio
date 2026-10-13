import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Mail, Phone } from "lucide-react";
import { z } from "zod";
import { Card, PageHeader } from "@/components/admin/page-header";
import { OrderStatusForm } from "@/components/admin/order-status-form";
import { OrderSummary } from "@/components/store/order-summary";
import { WhatsAppIcon } from "@/components/store/brand-icons";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { requireAdmin } from "@/lib/admin/auth";
import { toWhatsAppNumber } from "@/lib/argentina";
import { absoluteUrl } from "@/lib/env";
import { formatAddress, shippingAddressOf } from "@/lib/orders/queries";
import { ORDER_STATUS_LABEL, ORDER_STATUS_TONE } from "@/lib/orders/status";
import { formatDate, whatsappUrl } from "@/lib/utils";

export const metadata: Metadata = { title: "Pedido" };

export default async function AdminOrderPage({ params }: PageProps<"/admin/pedidos/[id]">) {
  const { supabase } = await requireAdmin();
  const id = z.uuid().safeParse((await params).id);
  if (!id.success) notFound();

  const { data: order, error } = await supabase
    .from("orders")
    .select("*, items:order_items(*)")
    .eq("id", id.data)
    .maybeSingle();
  if (error) throw new Error(`No se pudo leer el pedido: ${error.message}`);
  if (!order) notFound();
  const address = shippingAddressOf(order);
  const customerWhatsApp = toWhatsAppNumber(order.customer_phone);

  return (
    <>
      <Link
        href="/admin/pedidos"
        className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="size-4" aria-hidden /> Pedidos
      </Link>
      <PageHeader
        title={`Pedido #${order.number}`}
        description={`Creado el ${formatDate(order.created_at)}${order.paid_at ? ` · Pagado el ${formatDate(order.paid_at)}` : ""}`}
        actions={<Badge tone={ORDER_STATUS_TONE[order.status]}>{ORDER_STATUS_LABEL[order.status]}</Badge>}
      />
      {order.mp_payment_status &&
        ["refunded", "charged_back", "cancelled", "amount_mismatch"].includes(order.mp_payment_status) && (
          <Alert tone="error" title="Revisá el pago antes de despachar" className="mb-6">
            {order.mp_payment_status === "amount_mismatch"
              ? "El monto pagado en Mercado Pago no coincide con el total del pedido."
              : `Mercado Pago informa el pago como "${order.mp_payment_status}" (reintegro, contracargo o cancelación).`}
          </Alert>
        )}
      <div className="grid gap-6 lg:grid-cols-[1fr_22rem]">
        <div className="flex flex-col gap-6">
          <Card>
            <h2 className="mb-2 font-semibold">Productos</h2>
            <OrderSummary order={order} />
          </Card>
          <Card>
            <h2 className="mb-3 font-semibold">Entrega</h2>
            {order.delivery_method === "pickup" ? (
              <p className="text-sm">Retira en el local.</p>
            ) : (
              <p className="text-sm">
                Envío a {address ? formatAddress(address) : "—"}
                {order.shipping_zone && <span className="text-muted-foreground"> · Zona: {order.shipping_zone}</span>}
              </p>
            )}
            {order.notes && (
              <p className="mt-3 rounded-lg bg-muted p-3 text-sm">
                <span className="font-medium">Notas del cliente:</span> {order.notes}
              </p>
            )}
          </Card>
        </div>

        <div className="flex flex-col gap-6">
          <Card>
            <OrderStatusForm orderId={order.id} status={order.status} />
          </Card>
          <Card>
            <h2 className="mb-3 font-semibold">Cliente</h2>
            <div className="flex flex-col gap-2 text-sm">
              <p className="font-medium">{order.customer_name}</p>
              {order.customer_dni && <p className="text-muted-foreground">DNI {order.customer_dni}</p>}
              <a href={`mailto:${order.customer_email}`} className="flex items-center gap-2 hover:underline">
                <Mail className="size-4" aria-hidden /> {order.customer_email}
              </a>
              <a
                href={`tel:${order.customer_phone.replace(/[^\d+]/g, "")}`}
                className="flex items-center gap-2 hover:underline"
              >
                <Phone className="size-4" aria-hidden /> {order.customer_phone}
              </a>
              {customerWhatsApp && (
                <a
                  href={whatsappUrl(
                    `¡Hola ${order.customer_name.split(" ")[0]}! Te escribimos por tu pedido #${order.number}.`,
                    customerWhatsApp,
                  )}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-[#128c4a] hover:underline"
                >
                  <WhatsAppIcon width={16} height={16} /> Escribirle por WhatsApp
                </a>
              )}
            </div>
          </Card>
          <Card>
            <h2 className="mb-3 font-semibold">Pago (Mercado Pago)</h2>
            <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
              <dt className="text-muted-foreground">Estado</dt>
              <dd>{order.mp_payment_status ?? "Sin pago registrado"}</dd>
              {order.mp_payment_status_detail && (
                <>
                  <dt className="text-muted-foreground">Detalle</dt>
                  <dd className="break-all">{order.mp_payment_status_detail}</dd>
                </>
              )}
              {order.mp_payment_id && (
                <>
                  <dt className="text-muted-foreground">ID de pago</dt>
                  <dd className="break-all">{order.mp_payment_id}</dd>
                </>
              )}
            </dl>
            <a
              href={absoluteUrl(`/pedido/${order.id}?token=${order.access_token}`)}
              target="_blank"
              rel="noreferrer"
              className="mt-3 inline-block text-sm underline underline-offset-4"
            >
              Ver como el cliente
            </a>
          </Card>
        </div>
      </div>
    </>
  );
}
