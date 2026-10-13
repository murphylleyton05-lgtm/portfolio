import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { CircleCheck, Clock } from "lucide-react";
import { z } from "zod";
import { siteConfig } from "@site-config";
import { OrderSummary } from "@/components/store/order-summary";
import { WhatsAppLink } from "@/components/store/whatsapp-button";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/alert";
import { Button, buttonClasses } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { startPayment } from "@/lib/actions/checkout";
import { canCreateOrders, isMercadoPagoConfigured } from "@/lib/env.server";
import { syncPendingOrder } from "@/lib/orders/sync";
import { formatAddress, getOrderForCustomer, shippingAddressOf } from "@/lib/orders/queries";
import { ORDER_STATUS_LABEL, ORDER_STATUS_MESSAGE, ORDER_STATUS_TONE } from "@/lib/orders/status";
import { formatDate } from "@/lib/utils";

export const metadata: Metadata = { title: "Tu pedido", robots: { index: false, follow: false } };

const paramsSchema = z.object({ id: z.uuid(), token: z.uuid() });

export default function OrderPage({ params, searchParams }: PageProps<"/pedido/[id]">) {
  return (
    <div className="container-page max-w-3xl py-8">
      <Suspense fallback={<OrderSkeleton />}>
        <OrderView params={params} searchParams={searchParams} />
      </Suspense>
    </div>
  );
}

async function OrderView({ params, searchParams }: PageProps<"/pedido/[id]">) {
  const [{ id }, query] = await Promise.all([params, searchParams]);
  const parsed = paramsSchema.safeParse({ id, token: Array.isArray(query.token) ? query.token[0] : query.token });
  if (!parsed.success || !canCreateOrders) notFound();

  let order = await getOrderForCustomer(parsed.data.id, parsed.data.token);
  if (!order) notFound();

  const first = (value: string | string[] | undefined) => (Array.isArray(value) ? value[0] : value);
  const sync = await syncPendingOrder(order, first(query.payment_id) ?? first(query.collection_id));
  if (sync) order = (await getOrderForCustomer(order.id, order.access_token)) ?? order;

  const address = shippingAddressOf(order);
  const paid = order.status !== "pending_payment" && order.status !== "cancelled";

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-3">
        {paid ? (
          <CircleCheck className="size-10 text-emerald-600" aria-hidden />
        ) : (
          <Clock className="size-10 text-amber-600" aria-hidden />
        )}
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Pedido #{order.number}</h1>
          <Badge tone={ORDER_STATUS_TONE[order.status]}>{ORDER_STATUS_LABEL[order.status]}</Badge>
        </div>
        <p className="text-muted-foreground">{ORDER_STATUS_MESSAGE[order.status]}</p>
        <p className="text-sm text-muted-foreground">
          Realizado el {formatDate(order.created_at)} · Te enviamos los detalles a <strong>{order.customer_email}</strong>
        </p>
      </header>

      {order.status === "pending_payment" && <PaymentBox order={order} />}

      <section aria-labelledby="detalle" className="rounded-2xl border border-border p-6">
        <h2 id="detalle" className="mb-2 font-semibold">
          Detalle
        </h2>
        <OrderSummary order={order} />
      </section>

      <section aria-labelledby="entrega" className="rounded-2xl border border-border p-6 text-sm">
        <h2 id="entrega" className="mb-2 font-semibold">
          Entrega
        </h2>
        {order.delivery_method === "pickup" ? (
          <p>
            Retiro en {siteConfig.pickup.address} · {siteConfig.pickup.hours}. {siteConfig.pickup.instructions}
          </p>
        ) : (
          <p>Envío a {address ? formatAddress(address) : "la dirección indicada"}.</p>
        )}
        {order.notes && <p className="mt-2 text-muted-foreground">Notas: {order.notes}</p>}
      </section>

      <div className="flex flex-wrap gap-3">
        <Link href="/productos" className={buttonClasses("outline")}>
          Seguir comprando
        </Link>
        <WhatsAppLink message={`¡Hola! Te escribo por mi pedido #${order.number}.`} label="Consultar por mi pedido" />
        <a href={`mailto:${siteConfig.contact.email}?subject=Pedido%20%23${order.number}`} className={buttonClasses("ghost")}>
          Escribinos por email
        </a>
      </div>
    </div>
  );
}

function PaymentBox({ order }: { order: NonNullable<Awaited<ReturnType<typeof getOrderForCustomer>>> }) {
  const paymentStatus = order.mp_payment_status;
  if (!isMercadoPagoConfigured) {
    return (
      <Alert tone="info" title="Te vamos a contactar para coordinar el pago">
        Recibimos tu pedido. En breve te escribimos a {order.customer_email} o por WhatsApp.
      </Alert>
    );
  }
  if (paymentStatus === "pending" || paymentStatus === "in_process" || paymentStatus === "authorized") {
    return (
      <Alert tone="info" title="Tu pago está en proceso">
        Si pagaste en efectivo o por transferencia puede tardar hasta 48 hs en acreditarse. Te avisamos por email cuando se
        confirme.
      </Alert>
    );
  }
  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-amber-200 bg-amber-50 p-6">
      <p className="text-sm text-amber-900">
        {paymentStatus === "rejected" || paymentStatus === "cancelled"
          ? "Tu pago no se pudo completar. Podés intentarlo de nuevo con otro medio de pago."
          : "Todavía no registramos el pago de este pedido."}
      </p>
      {order.mp_init_point ? (
        <a href={order.mp_init_point} className={buttonClasses("primary", "lg", "w-full sm:w-auto")}>
          Pagar con Mercado Pago
        </a>
      ) : (
        <form action={startPayment}>
          <input type="hidden" name="orderId" value={order.id} />
          <input type="hidden" name="token" value={order.access_token} />
          <Button type="submit" size="lg" className="w-full sm:w-auto">
            Pagar con Mercado Pago
          </Button>
        </form>
      )}
    </div>
  );
}

function OrderSkeleton() {
  return (
    <div role="status" aria-label="Cargando pedido" className="flex flex-col gap-4">
      <Skeleton className="size-10 rounded-full" />
      <Skeleton className="h-8 w-56" />
      <Skeleton className="h-4 w-80" />
      <Skeleton className="h-64 rounded-2xl" />
    </div>
  );
}
