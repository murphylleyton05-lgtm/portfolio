import type { Metadata } from "next";
import Link from "next/link";
import { Card, PageHeader } from "@/components/admin/page-header";
import { Badge } from "@/components/ui/badge";
import { requireAdmin } from "@/lib/admin/auth";
import { getDashboardData } from "@/lib/admin/dashboard";
import { ORDER_STATUS_LABEL, ORDER_STATUS_TONE } from "@/lib/orders/status";
import { formatDate, formatPrice } from "@/lib/utils";

export const metadata: Metadata = { title: "Inicio" };

export default async function AdminHome() {
  const { supabase } = await requireAdmin();
  const data = await getDashboardData(supabase);
  const stats = [
    { label: "Para preparar", value: String(data.toPrepareCount), href: "/admin/pedidos?estado=paid" },
    { label: "Esperando pago", value: String(data.pendingCount), href: "/admin/pedidos?estado=pending_payment" },
    { label: "Vendido (30 días)", value: formatPrice(data.salesTotal), href: "/admin/pedidos" },
    { label: "Pedidos pagos (30 días)", value: String(data.salesCount), href: "/admin/pedidos" },
  ];

  return (
    <>
      <PageHeader title="Inicio" description="Resumen de la tienda." />
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {stats.map((stat) => (
          <Link key={stat.label} href={stat.href} className="rounded-xl border border-border bg-background p-4 transition hover:border-primary">
            <p className="text-sm text-muted-foreground">{stat.label}</p>
            <p className="mt-1 text-2xl font-semibold tabular-nums">{stat.value}</p>
          </Link>
        ))}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_22rem]">
        <Card>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-semibold">Últimos pedidos</h2>
            <Link href="/admin/pedidos" className="text-sm underline-offset-4 hover:underline">
              Ver todos
            </Link>
          </div>
          {data.recentOrders.length ? (
            <ul className="divide-y divide-border">
              {data.recentOrders.map((order) => (
                <li key={order.id}>
                  <Link href={`/admin/pedidos/${order.id}`} className="flex flex-wrap items-center gap-x-4 gap-y-1 py-3 text-sm hover:bg-muted/50">
                    <span className="font-medium">#{order.number}</span>
                    <span className="flex-1 truncate">{order.customer_name}</span>
                    <Badge tone={ORDER_STATUS_TONE[order.status]}>{ORDER_STATUS_LABEL[order.status]}</Badge>
                    <span className="w-24 text-right tabular-nums">{formatPrice(order.total)}</span>
                    <span className="w-full text-xs text-muted-foreground sm:w-auto">{formatDate(order.created_at)}</span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">Todavía no hay pedidos.</p>
          )}
        </Card>

        <Card>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-semibold">Stock bajo</h2>
            <Link href="/admin/stock?bajo=1" className="text-sm underline-offset-4 hover:underline">
              Gestionar
            </Link>
          </div>
          {data.lowStock.length ? (
            <ul className="flex flex-col gap-2 text-sm">
              {data.lowStock.map((variant) => (
                <li key={variant.id} className="flex justify-between gap-3">
                  <span className="truncate">
                    {variant.product?.name}
                    {variant.name !== "Único" && <span className="text-muted-foreground"> · {variant.name}</span>}
                  </span>
                  <Badge tone={variant.stock === 0 ? "danger" : "warning"}>{variant.stock}</Badge>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">Todo con stock. 🎉</p>
          )}
        </Card>
      </div>
    </>
  );
}
