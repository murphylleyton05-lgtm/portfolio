import { z } from "zod";
import { publicEnv } from "@/lib/env";
import { ORDER_STATUSES } from "@/lib/orders/status";
import type { OrderStatus } from "@/lib/supabase/database.types";

export const PRODUCT_IMAGES_BUCKET = "product-images";

/** URL pública base del bucket de imágenes (Supabase Storage). */
export function storagePublicPrefix() {
  return publicEnv.supabaseUrl ? `${publicEnv.supabaseUrl}/storage/v1/object/public/${PRODUCT_IMAGES_BUCKET}/` : null;
}

/** Ruta dentro del bucket a partir de la URL pública (null si no es nuestra). */
export function storagePathFromUrl(url: string) {
  const prefix = storagePublicPrefix();
  return prefix && url.startsWith(prefix) ? decodeURIComponent(url.slice(prefix.length)) : null;
}

/** Solo se aceptan imágenes propias: de /public o del bucket de Storage. */
function isAllowedImage(url: string) {
  return /^\/[\w\-./]+$/.test(url) || storagePathFromUrl(url) !== null;
}

const emptyToUndefined = (value: unknown) =>
  value === "" || value === null || (typeof value === "number" && Number.isNaN(value)) ? undefined : value;

const money = z.coerce
  .number({ error: "Ingresá un número" })
  .min(0, "No puede ser negativo")
  .max(99_999_999, "Demasiado alto");

const optionalMoney = z.preprocess(emptyToUndefined, money.optional());

const slug = z
  .string()
  .trim()
  .toLowerCase()
  .min(1, "Requerido")
  .max(80, "Máximo 80 caracteres")
  .regex(/^[a-z0-9]+(-[a-z0-9]+)*$/, "Solo minúsculas, números y guiones (ej: remera-negra)");

export const variantInputSchema = z.object({
  id: z.preprocess(emptyToUndefined, z.uuid().optional()),
  name: z.string().trim().min(1, "Requerido").max(80, "Máximo 80 caracteres"),
  sku: z.preprocess(emptyToUndefined, z.string().trim().max(60, "Máximo 60 caracteres").optional()),
  price: optionalMoney,
  stock: z.coerce
    .number({ error: "Ingresá un número" })
    .int("Sin decimales")
    .min(0, "No puede ser negativo")
    .max(1_000_000),
});

export const productFormSchema = z
  .object({
    id: z.preprocess(emptyToUndefined, z.uuid().optional()),
    name: z.string().trim().min(2, "Mínimo 2 caracteres").max(120, "Máximo 120 caracteres"),
    slug,
    description: z.string().trim().max(5000, "Máximo 5000 caracteres"),
    categoryId: z.preprocess(emptyToUndefined, z.uuid().optional()),
    price: money,
    compareAtPrice: optionalMoney,
    active: z.boolean(),
    featured: z.boolean(),
    images: z.array(z.string().refine(isAllowedImage, "Imagen no permitida")).max(10, "Máximo 10 imágenes"),
    variants: z.array(variantInputSchema).min(1, "Agregá al menos una variante").max(50, "Máximo 50 variantes"),
  })
  .superRefine((data, ctx) => {
    if (data.compareAtPrice !== undefined && data.compareAtPrice <= data.price) {
      ctx.addIssue({
        code: "custom",
        path: ["compareAtPrice"],
        message: "Tiene que ser mayor al precio (es el precio tachado)",
      });
    }
    const names = new Set<string>();
    const skus = new Set<string>();
    data.variants.forEach((variant, index) => {
      const name = variant.name.toLowerCase();
      if (names.has(name))
        ctx.addIssue({ code: "custom", path: ["variants", index, "name"], message: "Nombre repetido" });
      names.add(name);
      if (variant.sku) {
        const sku = variant.sku.toLowerCase();
        if (skus.has(sku)) ctx.addIssue({ code: "custom", path: ["variants", index, "sku"], message: "SKU repetido" });
        skus.add(sku);
      }
    });
  });

export type ProductFormInput = z.input<typeof productFormSchema>;
export type ProductFormValues = z.output<typeof productFormSchema>;

export const stockUpdateSchema = z.object({
  variantId: z.uuid(),
  stock: z.coerce
    .number({ error: "Ingresá un número" })
    .int("Sin decimales")
    .min(0, "No puede ser negativo")
    .max(1_000_000),
});

export const orderStatusSchema = z.object({
  orderId: z.uuid(),
  status: z.enum(ORDER_STATUSES as [OrderStatus, ...OrderStatus[]]),
});

export const categorySchema = z.object({
  id: z.preprocess(emptyToUndefined, z.uuid().optional()),
  name: z.string().trim().min(2, "Mínimo 2 caracteres").max(80, "Máximo 80 caracteres"),
  slug,
  description: z.string().trim().max(300, "Máximo 300 caracteres"),
  position: z.coerce.number().int().min(0).max(1000),
});

/** Convierte errores de Zod en { "campo.sub": "mensaje" } para los formularios. */
export function fieldErrorsOf(error: z.ZodError) {
  const fieldErrors: Record<string, string> = {};
  for (const issue of error.issues) fieldErrors[issue.path.join(".")] ??= issue.message;
  return fieldErrors;
}
