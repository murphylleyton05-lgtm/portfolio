import type { Metadata } from "next";
import Link from "next/link";
import { z } from "zod";
import { siteConfig } from "@site-config";
import { Card, PageHeader } from "@/components/admin/page-header";
import { StockRowForm } from "@/components/admin/stock-row-form";
import { Badge } from "@/components/ui/badge";
import { requireAdmin } from "@/lib/admin/auth";
import { cn } from "@/lib/utils";

export const metadata: Metadata = { title: "Stock" };

const first = (value: unknown) => (Array.isArray(value) ? value[0] : value);
const querySchema = z.object({ bajo: z.preprocess(first, z.literal("1").optional()).catch(undefined) });

export default async function StockPage({ searchParams }: PageProps<"/admin/stock">) {
  const { supabase } = await requireAdmin();
  const { bajo } = querySchema.parse(await searchParams);
  const threshold = siteConfig.catalog.lowStockThreshold;

  let query = supabase.from("product_variants").select("id, name, sku, stock, product:products(id, name, active)");
  if (bajo) query = query.lte("stock", threshold);
  const { data, error } = await query;
  if (error) throw new Error(`No se pudo leer el stock: ${error.message}`);

  const rows = [...data].sort(
    (a, b) => (a.product?.name ?? "").localeCompare(b.product?.name ?? "", "es") || a.name.localeCompare(b.name, "es"),
  );

  return (
    <>
      <PageHeader title="Stock" description={`Las variantes con ${threshold} unidades o menos se marcan como stock bajo.`} />
      <div className="mb-4 flex gap-2">
        <Link href="/admin/stock" className={tab(!bajo)}>
          Todo
        </Link>
        <Link href="/admin/stock?bajo=1" className={tab(Boolean(bajo))}>
          Stock bajo
        </Link>
      </div>
      <Card className="overflow-x-auto p-0 sm:p-0">
        <table className="w-full min-w-[36rem] text-sm">
          <thead className="border-b border-border text-left text-muted-foreground">
            <tr>
              <th className="px-4 py-3 font-medium">Producto</th>
              <th className="px-4 py-3 font-medium">Variante</th>
              <th className="px-4 py-3 font-medium">SKU</th>
              <th className="px-4 py-3 text-right font-medium">Stock</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((variant) => (
              <tr key={variant.id}>
                <td className="px-4 py-2">
                  {variant.product ? (
                    <Link href={`/admin/productos/${variant.product.id}`} className="underline-offset-4 hover:underline">
                      {variant.product.name}
                    </Link>
                  ) : (
                    "—"
                  )}
                  {variant.product && !variant.product.active && (
                    <Badge tone="neutral" className="ml-2">
                      Pausado
                    </Badge>
                  )}
                </td>
                <td className="px-4 py-2">
                  {variant.name}
                  {variant.stock <= threshold && (
                    <Badge tone={variant.stock === 0 ? "danger" : "warning"} className="ml-2">
                      {variant.stock === 0 ? "Sin stock" : "Bajo"}
                    </Badge>
                  )}
                </td>
                <td className="px-4 py-2 text-muted-foreground">{variant.sku ?? "—"}</td>
                <td className="px-4 py-2">
                  <StockRowForm variantId={variant.id} stock={variant.stock} label={`${variant.product?.name ?? ""} ${variant.name}`} />
                </td>
              </tr>
            ))}
            {!rows.length && (
              <tr>
                <td colSpan={4} className="px-4 py-10 text-center text-muted-foreground">
                  {bajo ? "No hay variantes con stock bajo. 🎉" : "No hay variantes."}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </>
  );
}

function tab(active: boolean) {
  return cn(
    "rounded-full border px-3 py-1.5 text-sm",
    active ? "border-primary bg-primary text-primary-foreground" : "border-border bg-background hover:border-primary",
  );
}
