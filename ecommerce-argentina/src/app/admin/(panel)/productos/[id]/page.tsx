import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { z } from "zod";
import { PageHeader } from "@/components/admin/page-header";
import { DeleteProductButton } from "@/components/admin/delete-product-button";
import { ProductForm } from "@/components/admin/product-form";
import { buttonClasses } from "@/components/ui/button";
import { requireAdmin } from "@/lib/admin/auth";

export const metadata: Metadata = { title: "Editar producto" };

export default async function EditProductPage({ params }: PageProps<"/admin/productos/[id]">) {
  const { supabase } = await requireAdmin();
  const id = z.uuid().safeParse((await params).id);
  if (!id.success) notFound();

  const [{ data: product, error }, { data: categories }] = await Promise.all([
    supabase.from("products").select("*, variants:product_variants(*)").eq("id", id.data).maybeSingle(),
    supabase.from("categories").select("id, name").order("position").order("name"),
  ]);
  if (error) throw new Error(`No se pudo leer el producto: ${error.message}`);
  if (!product) notFound();

  return (
    <>
      <Link
        href="/admin/productos"
        className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="size-4" aria-hidden /> Productos
      </Link>
      <PageHeader
        title={product.name}
        actions={
          <>
            <Link href={`/productos/${product.slug}`} target="_blank" className={buttonClasses("outline", "sm")}>
              <ExternalLink className="size-4" aria-hidden /> Ver en la tienda
            </Link>
            <DeleteProductButton id={product.id} name={product.name} />
          </>
        }
      />
      <ProductForm
        categories={categories ?? []}
        product={{
          id: product.id,
          name: product.name,
          slug: product.slug,
          description: product.description,
          categoryId: product.category_id ?? "",
          price: Number(product.price),
          compareAtPrice: product.compare_at_price === null ? "" : Number(product.compare_at_price),
          active: product.active,
          featured: product.featured,
          images: product.images,
          variants: [...product.variants]
            .sort((a, b) => a.position - b.position)
            .map((variant) => ({
              id: variant.id,
              name: variant.name,
              sku: variant.sku ?? "",
              price: variant.price === null ? "" : Number(variant.price),
              stock: variant.stock,
            })),
        }}
      />
    </>
  );
}
