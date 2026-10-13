"use server";

import { randomUUID } from "node:crypto";
import { revalidatePath, updateTag } from "next/cache";
import { redirect } from "next/navigation";
import { z } from "zod";
import { requireAdminAction, UnauthorizedError } from "@/lib/admin/auth";
import { PRODUCT_IMAGES_BUCKET, fieldErrorsOf, productFormSchema, storagePathFromUrl } from "@/lib/admin/schemas";
import { CATALOG_TAG } from "@/lib/catalog/data";

export type SaveProductResult =
  { ok: true; id: string; variantIds: string[] } | { ok: false; error: string; fieldErrors?: Record<string, string> };

const UNIQUE_VIOLATION = "23505";

export async function saveProduct(input: unknown): Promise<SaveProductResult> {
  let session;
  try {
    session = await requireAdminAction();
  } catch (error) {
    if (error instanceof UnauthorizedError) return { ok: false, error: "Tu sesión expiró. Volvé a ingresar." };
    throw error;
  }
  const { supabase } = session;

  const parsed = productFormSchema.safeParse(input);
  if (!parsed.success)
    return { ok: false, error: "Revisá los campos marcados.", fieldErrors: fieldErrorsOf(parsed.error) };
  const data = parsed.data;

  const row = {
    name: data.name,
    slug: data.slug,
    description: data.description,
    category_id: data.categoryId ?? null,
    price: data.price,
    compare_at_price: data.compareAtPrice ?? null,
    active: data.active,
    featured: data.featured,
    images: data.images,
  };

  let productId = data.id;
  let previousImages: string[] = [];
  if (productId) {
    const { data: existing, error } = await supabase
      .from("products")
      .select("images")
      .eq("id", productId)
      .maybeSingle();
    if (error || !existing) return { ok: false, error: "El producto ya no existe." };
    previousImages = existing.images;
    const { error: updateError } = await supabase.from("products").update(row).eq("id", productId);
    if (updateError) return productError(updateError);
  } else {
    const { data: created, error } = await supabase.from("products").insert(row).select("id").single();
    if (error) return productError(error);
    productId = created.id;
  }

  // Variantes: actualizar las existentes, crear las nuevas y borrar las que se quitaron.
  const { data: existingVariants, error: variantsError } = await supabase
    .from("product_variants")
    .select("id")
    .eq("product_id", productId);
  if (variantsError) return { ok: false, error: "No se pudieron leer las variantes." };

  const existingIds = new Set(existingVariants.map((variant) => variant.id));
  const rows = data.variants.map((variant, position) => ({
    // Un id que no pertenece a este producto se trata como variante nueva.
    id: variant.id && existingIds.has(variant.id) ? variant.id : randomUUID(),
    product_id: productId,
    name: variant.name,
    sku: variant.sku ?? null,
    price: variant.price ?? null,
    stock: variant.stock,
    position,
  }));
  const keep = new Set(rows.map((row) => row.id));
  const toDelete = [...existingIds].filter((id) => !keep.has(id));

  if (toDelete.length) {
    const { error } = await supabase.from("product_variants").delete().in("id", toDelete);
    if (error) return { ok: false, error: "No se pudieron borrar variantes." };
  }
  const { error: upsertError } = await supabase.from("product_variants").upsert(rows, { onConflict: "id" });
  if (upsertError) {
    if (upsertError.code === UNIQUE_VIOLATION) {
      return {
        ok: false,
        error: "Hay un SKU que ya usa otro producto.",
        fieldErrors: { variants: "SKU repetido en otro producto" },
      };
    }
    console.error("[saveProduct] variants", upsertError);
    return { ok: false, error: "No se pudieron guardar las variantes." };
  }

  // Borrar del Storage las imágenes que se quitaron (si son nuestras).
  const removed = previousImages
    .filter((url) => !data.images.includes(url))
    .map(storagePathFromUrl)
    .filter((path): path is string => Boolean(path));
  if (removed.length) await supabase.storage.from(PRODUCT_IMAGES_BUCKET).remove(removed);

  updateTag(CATALOG_TAG);
  revalidatePath("/admin/productos");
  return { ok: true, id: productId, variantIds: rows.map((row) => row.id) };
}

function productError(error: { code?: string; message: string }): SaveProductResult {
  if (error.code === UNIQUE_VIOLATION) {
    return {
      ok: false,
      error: "Ya existe un producto con ese slug.",
      fieldErrors: { slug: "Ya existe un producto con ese slug" },
    };
  }
  console.error("[saveProduct]", error);
  return { ok: false, error: "No se pudo guardar el producto." };
}

const idSchema = z.uuid();

export async function deleteProduct(formData: FormData): Promise<void> {
  const { supabase } = await requireAdminAction();
  const id = idSchema.parse(formData.get("id"));
  const { data: product } = await supabase.from("products").select("images").eq("id", id).maybeSingle();
  const { error } = await supabase.from("products").delete().eq("id", id);
  if (error) throw new Error(`No se pudo borrar el producto: ${error.message}`);
  const paths = (product?.images ?? []).map(storagePathFromUrl).filter((path): path is string => Boolean(path));
  if (paths.length) await supabase.storage.from(PRODUCT_IMAGES_BUCKET).remove(paths);
  updateTag(CATALOG_TAG);
  redirect("/admin/productos");
}

export async function setProductActive(formData: FormData): Promise<void> {
  const { supabase } = await requireAdminAction();
  const { id, active } = z
    .object({ id: z.uuid(), active: z.enum(["true", "false"]).transform((v) => v === "true") })
    .parse({ id: formData.get("id"), active: formData.get("active") });
  const { error } = await supabase.from("products").update({ active }).eq("id", id);
  if (error) throw new Error(`No se pudo actualizar: ${error.message}`);
  updateTag(CATALOG_TAG);
  revalidatePath("/admin/productos");
}
