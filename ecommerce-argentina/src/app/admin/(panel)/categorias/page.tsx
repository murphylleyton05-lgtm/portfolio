import type { Metadata } from "next";
import { Trash2 } from "lucide-react";
import { Card, PageHeader } from "@/components/admin/page-header";
import { CategoryForm } from "@/components/admin/category-form";
import { ConfirmForm } from "@/components/admin/confirm-form";
import { Button } from "@/components/ui/button";
import { deleteCategory } from "@/lib/actions/admin/categories";
import { requireAdmin } from "@/lib/admin/auth";

export const metadata: Metadata = { title: "Categorías" };

export default async function CategoriesPage() {
  const { supabase } = await requireAdmin();
  const { data: categories, error } = await supabase
    .from("categories")
    .select("id, name, slug, description, position, products(count)")
    .order("position")
    .order("name");
  if (error) throw new Error(`No se pudieron leer las categorías: ${error.message}`);

  return (
    <>
      <PageHeader title="Categorías" description="Ordenan el menú y los filtros de la tienda." />
      <Card className="mb-6">
        <h2 className="mb-3 font-semibold">Nueva categoría</h2>
        <CategoryForm />
      </Card>
      <div className="flex flex-col gap-3">
        {categories.map((category) => (
          <Card key={category.id}>
            <div className="mb-3 flex items-center justify-between gap-3">
              <p className="text-sm text-muted-foreground">{category.products[0]?.count ?? 0} productos</p>
              <ConfirmForm
                action={deleteCategory}
                message={`¿Borrar la categoría "${category.name}"? Sus productos quedan sin categoría.`}
              >
                <input type="hidden" name="id" value={category.id} />
                <Button type="submit" variant="ghost" size="sm" aria-label={`Borrar ${category.name}`}>
                  <Trash2 className="size-4" aria-hidden /> Borrar
                </Button>
              </ConfirmForm>
            </div>
            <CategoryForm category={category} />
          </Card>
        ))}
      </div>
    </>
  );
}
