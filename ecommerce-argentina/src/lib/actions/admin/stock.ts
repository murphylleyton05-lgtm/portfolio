"use server";

import { revalidatePath, updateTag } from "next/cache";
import { requireAdminAction } from "@/lib/admin/auth";
import { fieldErrorsOf, stockUpdateSchema } from "@/lib/admin/schemas";
import { CATALOG_TAG } from "@/lib/catalog/data";

export type StockState = { ok?: boolean; error?: string; stock?: number };

export async function updateStock(_prev: StockState, formData: FormData): Promise<StockState> {
  const { supabase } = await requireAdminAction();
  const parsed = stockUpdateSchema.safeParse({ variantId: formData.get("variantId"), stock: formData.get("stock") });
  if (!parsed.success) return { error: Object.values(fieldErrorsOf(parsed.error))[0] };

  const { error } = await supabase.from("product_variants").update({ stock: parsed.data.stock }).eq("id", parsed.data.variantId);
  if (error) return { error: "No se pudo guardar." };
  updateTag(CATALOG_TAG);
  revalidatePath("/admin/stock");
  return { ok: true, stock: parsed.data.stock };
}
