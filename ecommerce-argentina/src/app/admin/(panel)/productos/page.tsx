import type { Metadata } from "next";
import Form from "next/form";
import Image from "next/image";
import Link from "next/link";
import { Plus } from "lucide-react";
import { z } from "zod";
import { siteConfig } from "@site-config";
import { Card, PageHeader } from "@/components/admin/page-header";
import { Badge } from "@/components/ui/badge";
import { Button, buttonClasses } from "@/components/ui/button";
import { Input } from "@/components/ui/field";
import { setProductActive } from "@/lib/actions/admin/products";
import { requireAdmin } from "@/lib/admin/auth";
import { formatPrice, normalizeText } from "@/lib/utils";

export const metadata: Metadata = { title: "Productos" };

const first = (value: unknown) => (Array.isArray(value) ? value[0] : value);
const querySchema = z.object({
  q: z.preprocess(first, z.string().trim().max(80).optional()).catch(undefined),
});

export default async function AdminProductsPage({ searchParams }: PageProps<"/admin/productos">) {
  const { supabase } = await requireAdmin();
  const { q } = querySchema.parse(await searchParams);

  const { data, error } = await supabase
    .from("products")
    .select(
      "id, name, slug, price, active, featured, images, category:categories(name), variants:product_variants(stock)",
    )
    .order("created_at", { ascending: false });
  if (error) throw new Error(`No se pudieron leer los productos: ${error.message}`);

  const term = q ? normalizeText(q) : "";
  const products = term ? data.filter((p) => normalizeText(`${p.name} ${p.slug}`).includes(term)) : data;

  return (
    <>
      <PageHeader
        title="Productos"
        description={`${data.length} productos`}
        actions={
          <Link href="/admin/productos/nuevo" className={buttonClasses("primary")}>
            <Plus className="size-4" aria-hidden /> Nuevo producto
          </Link>
        }
      />
      <Form action="/admin/productos" className="mb-4 flex gap-2">
        <label htmlFor="q" className="sr-only">
          Buscar productos
        </label>
        <Input id="q" name="q" defaultValue={q} placeholder="Buscar por nombre" className="max-w-sm bg-background" />
        <Button type="submit" variant="outline">
          Buscar
        </Button>
      </Form>
      <Card className="p-0 sm:p-0">
        <ul className="divide-y divide-border">
          {products.map((product) => {
            const stock = product.variants.reduce((sum, v) => sum + v.stock, 0);
            return (
              <li key={product.id} className="flex items-center gap-3 px-4 py-3">
                <div className="relative aspect-[4/5] w-12 shrink-0 overflow-hidden rounded-md bg-muted">
                  {product.images[0] && (
                    <Image src={product.images[0]} alt="" fill sizes="48px" unoptimized className="object-cover" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <Link
                    href={`/admin/productos/${product.id}`}
                    className="font-medium underline-offset-4 hover:underline"
                  >
                    {product.name}
                  </Link>
                  <p className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    {product.category?.name ?? "Sin categoría"} · {formatPrice(product.price)} · Stock {stock}
                    {!product.active && <Badge tone="neutral">Pausado</Badge>}
                    {product.featured && <Badge tone="info">Destacado</Badge>}
                    {stock <= siteConfig.catalog.lowStockThreshold && (
                      <Badge tone={stock === 0 ? "danger" : "warning"}>Stock bajo</Badge>
                    )}
                  </p>
                </div>
                <form action={setProductActive}>
                  <input type="hidden" name="id" value={product.id} />
                  <input type="hidden" name="active" value={String(!product.active)} />
                  <Button type="submit" variant="ghost" size="sm">
                    {product.active ? "Pausar" : "Activar"}
                  </Button>
                </form>
                <Link href={`/admin/productos/${product.id}`} className={buttonClasses("outline", "sm")}>
                  Editar
                </Link>
              </li>
            );
          })}
          {!products.length && (
            <li className="px-4 py-10 text-center text-sm text-muted-foreground">No hay productos.</li>
          )}
        </ul>
      </Card>
    </>
  );
}
