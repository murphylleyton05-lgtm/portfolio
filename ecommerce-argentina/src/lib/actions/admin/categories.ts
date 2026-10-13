"use server";

import { revalidatePath, updateTag } from "next/cache";
import { z } from "zod";
import { requireAdminAction } from "@/lib/admin/auth";
import { categorySchema, fieldErrorsOf } from "@/lib/admin/schemas";
import { CATALOG_TAG } from "@/lib/catalog/data";

export type CategoryState = { ok?: boolean; error?: string; fieldErrors?: Record<string, string> };

export async function saveCategory(_prev: CategoryState, formData: FormData): Promise<CategoryState> {
  const { supabase } = await requireAdminAction();
  const parsed = categorySchema.safeParse({
    id: formData.get("id"),
    name: formData.get("name"),
    slug: formData.get("slug"),
    description: formData.get("description") ?? "",
    position: formData.get("position") || 0,
  });
  if (!parsed.success) return { error: "Revisá los campos.", fieldErrors: fieldErrorsOf(parsed.error) };

  const { id, ...row } = parsed.data;
  const { error } = id
    ? await supabase.from("categories").update(row).eq("id", id)
    : await supabase.from("categories").insert(row);
  if (error) {
    if (error.code === "23505")
      return { error: "Ya existe una categoría con ese slug.", fieldErrors: { slug: "Slug repetido" } };
    return { error: "No se pudo guardar la categoría." };
  }
  updateTag(CATALOG_TAG);
  revalidatePath("/admin/categorias");
  return { ok: true };
}

export async function deleteCategory(formData: FormData): Promise<void> {
  const { supabase } = await requireAdminAction();
  const id = z.uuid().parse(formData.get("id"));
  // Los productos de la categoría quedan "sin categoría" (on delete set null).
  const { error } = await supabase.from("categories").delete().eq("id", id);
  if (error) throw new Error(`No se pudo borrar: ${error.message}`);
  updateTag(CATALOG_TAG);
  revalidatePath("/admin/categorias");
}
