import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/page-header";
import { ProductForm } from "@/components/admin/product-form";
import { requireAdmin } from "@/lib/admin/auth";

export const metadata: Metadata = { title: "Nuevo producto" };

export default async function NewProductPage() {
  const { supabase } = await requireAdmin();
  const { data: categories } = await supabase.from("categories").select("id, name").order("position").order("name");
  return (
    <>
      <PageHeader title="Nuevo producto" />
      <ProductForm categories={categories ?? []} />
    </>
  );
}
