import type { Metadata } from "next";
import Form from "next/form";
import Link from "next/link";
import { z } from "zod";
import { Card, PageHeader } from "@/components/admin/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/field";
import { requireAdmin } from "@/lib/admin/auth";
import { ORDER_STATUSES, ORDER_STATUS_LABEL, ORDER_STATUS_TONE } from "@/lib/orders/status";
import type { OrderStatus } from "@/lib/supabase/database.types";
import { cn, formatDate, formatPrice } from "@/lib/utils";

export const metadata: Metadata = { title: "Pedidos" };

const PAGE_SIZE = 20;
const first = (value: unknown) => (Array.isArray(value) ? value[0] : value);
const querySchema = z.object({
  estado: z.preprocess(first, z.enum(ORDER_STATUSES as [OrderStatus, ...OrderStatus[]]).optional()).catch(undefined),
  q: z.preprocess(first, z.string().trim().max(80).optional()).catch(undefined),
  pagina: z.preprocess(first, z.coerce.number().int().min(1).max(10_000)).catch(1),
});

export default async function AdminOrdersPage({ searchParams }: PageProps<"/admin/pedidos">) {
  const { supabase } = await requireAdmin();
  const { estado, q, pagina } = querySchema.parse(await searchParams);

  let query = supabase
    .from("orders")
    .select("id, number, status, customer_name, customer_email, total, delivery_method, created_at", { count: "exact" })
    .order("created_at", { ascending: false })
    .range((pagina - 1) * PAGE_SIZE, pagina * PAGE_SIZE - 1);
  if (estado) query = query.eq("status", estado);
  if (q) {
    const number = q.replace(/^#/, "");
    if (/^\d+$/.test(number)) {
      query = query.eq("number", Number(number));
    } else {
      // Solo caracteres seguros para la sintaxis de filtros de PostgREST.
      const term = q.replace(/[^\p{L}\p{N}@._\- ]/gu, "").trim();
      if (term) query = query.or(`customer_email.ilike.*${term}*,customer_name.ilike.*${term}*`);
    }
  }
  const { data: orders, count, error } = await query;
  if (error) throw new Error(`No se pudieron leer los pedidos: ${error.message}`);
  const pageCount = Math.max(1, Math.ceil((count ?? 0) / PAGE_SIZE));

  const href = (changes: Record<string, string | number | undefined>) => {
    const params = new URLSearchParams();
    const merged = { estado, q, pagina: undefined as number | undefined, ...changes };
    for (const [key, value] of Object.entries(merged))
      if (value !== undefined && value !== "" && value !== 1) params.set(key, String(value));
    const search = params.toString();
    return search ? `/admin/pedidos?${search}` : "/admin/pedidos";
  };

  return (
    <>
      <PageHeader title="Pedidos" description={`${count ?? 0} pedidos`} />
      <div className="mb-4 flex flex-wrap gap-2">
        <Link href={href({ estado: undefined })} className={tab(!estado)}>
          Todos
        </Link>
        {ORDER_STATUSES.map((status) => (
          <Link key={status} href={href({ estado: status })} className={tab(estado === status)}>
            {ORDER_STATUS_LABEL[status]}
          </Link>
        ))}
      </div>
      <Form action="/admin/pedidos" className="mb-4 flex gap-2">
        {estado && <input type="hidden" name="estado" value={estado} />}
        <label htmlFor="q" className="sr-only">
          Buscar pedidos
        </label>
        <Input
          id="q"
          name="q"
          defaultValue={q}
          placeholder="Buscar por #número, nombre o email"
          className="max-w-sm bg-background"
        />
        <Button type="submit" variant="outline">
          Buscar
        </Button>
      </Form>

      <Card className="overflow-x-auto p-0 sm:p-0">
        <table className="w-full min-w-[40rem] text-sm">
          <thead className="border-b border-border text-left text-muted-foreground">
            <tr>
              <th className="px-4 py-3 font-medium">Pedido</th>
              <th className="px-4 py-3 font-medium">Cliente</th>
              <th className="px-4 py-3 font-medium">Estado</th>
              <th className="px-4 py-3 font-medium">Entrega</th>
              <th className="px-4 py-3 text-right font-medium">Total</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {orders.map((order) => (
              <tr key={order.id} className="hover:bg-muted/50">
                <td className="px-4 py-3">
                  <Link href={`/admin/pedidos/${order.id}`} className="font-medium underline-offset-4 hover:underline">
                    #{order.number}
                  </Link>
                  <p className="text-xs text-muted-foreground">{formatDate(order.created_at)}</p>
                </td>
                <td className="px-4 py-3">
                  <p>{order.customer_name}</p>
                  <p className="text-xs text-muted-foreground">{order.customer_email}</p>
                </td>
                <td className="px-4 py-3">
                  <Badge tone={ORDER_STATUS_TONE[order.status]}>{ORDER_STATUS_LABEL[order.status]}</Badge>
                </td>
                <td className="px-4 py-3">{order.delivery_method === "pickup" ? "Retiro" : "Envío"}</td>
                <td className="px-4 py-3 text-right tabular-nums">{formatPrice(order.total)}</td>
              </tr>
            ))}
            {!orders.length && (
              <tr>
                <td colSpan={5} className="px-4 py-10 text-center text-muted-foreground">
                  No hay pedidos{estado || q ? " con esos filtros" : " todavía"}.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>

      {pageCount > 1 && (
        <nav aria-label="Paginación" className="mt-4 flex items-center justify-between text-sm">
          {pagina > 1 ? <Link href={href({ pagina: pagina - 1 })}>← Anteriores</Link> : <span />}
          <span className="text-muted-foreground">
            Página {pagina} de {pageCount}
          </span>
          {pagina < pageCount ? <Link href={href({ pagina: pagina + 1 })}>Siguientes →</Link> : <span />}
        </nav>
      )}
    </>
  );
}

function tab(active: boolean) {
  return cn(
    "rounded-full border px-3 py-1.5 text-sm whitespace-nowrap",
    active ? "border-primary bg-primary text-primary-foreground" : "border-border bg-background hover:border-primary",
  );
}
