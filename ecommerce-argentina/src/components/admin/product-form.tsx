"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Controller, useFieldArray, useForm, type FieldErrors } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Trash2 } from "lucide-react";
import { saveProduct } from "@/lib/actions/admin/products";
import { productFormSchema, type ProductFormInput, type ProductFormValues } from "@/lib/admin/schemas";
import { slugify } from "@/lib/utils";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { Card } from "./page-header";
import { ImagesField } from "./images-field";

type Props = {
  categories: Array<{ id: string; name: string }>;
  product?: ProductFormInput & { id: string };
};

const emptyVariant = { name: "", sku: "", price: "", stock: 0 };

export function ProductForm({ categories, product }: Props) {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [slugTouched, setSlugTouched] = useState(Boolean(product));

  const { register, handleSubmit, control, setValue, setError, reset, formState } = useForm<
    ProductFormInput,
    unknown,
    ProductFormValues
  >({
    resolver: zodResolver(productFormSchema),
    mode: "onTouched",
    defaultValues: product ?? {
      name: "",
      slug: "",
      description: "",
      categoryId: categories[0]?.id ?? "",
      price: "",
      compareAtPrice: "",
      active: true,
      featured: false,
      images: [],
      variants: [{ ...emptyVariant, name: "Único" }],
    },
  });
  const { fields, append, remove } = useFieldArray({ control, name: "variants" });
  const errors = formState.errors as FieldErrors<ProductFormInput>;

  async function onSubmit(values: ProductFormValues) {
    setServerError(null);
    setSaved(false);
    const result = await saveProduct(values);
    if (!result.ok) {
      setServerError(result.error);
      for (const [name, message] of Object.entries(result.fieldErrors ?? {})) {
        setError(name as keyof ProductFormInput, { message });
      }
      return;
    }
    if (!product) {
      // Con Cache Components la página anterior queda "viva" al navegar:
      // limpiamos el formulario de alta para que no reaparezca lleno.
      reset();
      setSlugTouched(false);
      router.push(`/admin/productos/${result.id}`);
      return;
    }
    setSaved(true);
    // Las variantes nuevas ya tienen id en la base: lo guardamos en el form.
    result.variantIds.forEach((id, index) => setValue(`variants.${index}.id`, id));
    router.refresh();
  }

  const aria = (name: string, error?: { message?: string }) => ({
    id: name,
    "aria-invalid": error ? true : undefined,
    "aria-describedby": error ? `${name}-error` : undefined,
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-6">
      {serverError && <Alert tone="error">{serverError}</Alert>}
      {saved && <Alert tone="success">Producto guardado.</Alert>}

      <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
        <div className="flex flex-col gap-6">
          <Card>
            <div className="flex flex-col gap-4">
              <Field id="name" label="Nombre" error={errors.name?.message}>
                <Input
                  {...aria("name", errors.name)}
                  {...register("name", {
                    onChange: (event) => {
                      if (!slugTouched)
                        setValue("slug", slugify(event.target.value), { shouldValidate: formState.isSubmitted });
                    },
                  })}
                />
              </Field>
              <Field
                id="slug"
                label="URL (slug)"
                hint="Se usa en /productos/<slug>. Solo minúsculas, números y guiones."
                error={errors.slug?.message}
              >
                <Input {...aria("slug", errors.slug)} {...register("slug", { onChange: () => setSlugTouched(true) })} />
              </Field>
              <Field id="description" label="Descripción" error={errors.description?.message}>
                <Textarea {...aria("description", errors.description)} rows={6} {...register("description")} />
              </Field>
            </div>
          </Card>

          <Card>
            <h2 className="mb-3 font-semibold">Imágenes</h2>
            <Controller
              control={control}
              name="images"
              render={({ field }) => (
                <ImagesField value={field.value} onChange={field.onChange} error={errors.images?.message} />
              )}
            />
          </Card>

          <Card>
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <h2 className="font-semibold">Variantes y stock</h2>
                <p className="text-xs text-muted-foreground">
                  Talles, colores, etc. Si no tiene opciones, dejá una sola llamada &quot;Único&quot;.
                </p>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={() => append({ ...emptyVariant })}>
                <Plus className="size-4" aria-hidden /> Agregar variante
              </Button>
            </div>
            {errors.variants?.message && <p className="mb-2 text-sm text-red-600">{errors.variants.message}</p>}
            {errors.variants?.root?.message && (
              <p className="mb-2 text-sm text-red-600">{errors.variants.root.message}</p>
            )}
            <div className="flex flex-col gap-3">
              {fields.map((field, index) => {
                const fieldErrors = errors.variants?.[index];
                return (
                  <fieldset
                    key={field.id}
                    className="grid grid-cols-2 gap-3 rounded-lg border border-border p-3 sm:grid-cols-[1fr_1fr_8rem_6rem_auto]"
                  >
                    <legend className="sr-only">Variante {index + 1}</legend>
                    <input type="hidden" {...register(`variants.${index}.id`)} />
                    <Field id={`variants.${index}.name`} label="Nombre" error={fieldErrors?.name?.message}>
                      <Input
                        {...aria(`variants.${index}.name`, fieldErrors?.name)}
                        placeholder="M / Negro"
                        {...register(`variants.${index}.name`)}
                      />
                    </Field>
                    <Field id={`variants.${index}.sku`} label="SKU" error={fieldErrors?.sku?.message}>
                      <Input
                        {...aria(`variants.${index}.sku`, fieldErrors?.sku)}
                        placeholder="Opcional"
                        {...register(`variants.${index}.sku`)}
                      />
                    </Field>
                    <Field id={`variants.${index}.price`} label="Precio propio" error={fieldErrors?.price?.message}>
                      <Input
                        {...aria(`variants.${index}.price`, fieldErrors?.price)}
                        type="number"
                        inputMode="decimal"
                        min={0}
                        step="0.01"
                        placeholder="= producto"
                        {...register(`variants.${index}.price`)}
                      />
                    </Field>
                    <Field id={`variants.${index}.stock`} label="Stock" error={fieldErrors?.stock?.message}>
                      <Input
                        {...aria(`variants.${index}.stock`, fieldErrors?.stock)}
                        type="number"
                        inputMode="numeric"
                        min={0}
                        step={1}
                        {...register(`variants.${index}.stock`)}
                      />
                    </Field>
                    <div className="flex items-end">
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        aria-label={`Quitar variante ${index + 1}`}
                        disabled={fields.length === 1}
                        onClick={() => remove(index)}
                      >
                        <Trash2 className="size-4" aria-hidden />
                      </Button>
                    </div>
                  </fieldset>
                );
              })}
            </div>
          </Card>
        </div>

        <div className="flex flex-col gap-6">
          <Card>
            <div className="flex flex-col gap-4">
              <Field id="price" label="Precio (ARS)" error={errors.price?.message}>
                <Input
                  {...aria("price", errors.price)}
                  type="number"
                  inputMode="decimal"
                  min={0}
                  step="0.01"
                  {...register("price")}
                />
              </Field>
              <Field
                id="compareAtPrice"
                label="Precio anterior (tachado)"
                hint="Opcional. Muestra la oferta."
                error={errors.compareAtPrice?.message}
              >
                <Input
                  {...aria("compareAtPrice", errors.compareAtPrice)}
                  type="number"
                  inputMode="decimal"
                  min={0}
                  step="0.01"
                  {...register("compareAtPrice")}
                />
              </Field>
              <Field id="categoryId" label="Categoría" error={errors.categoryId?.message}>
                <Select {...aria("categoryId", errors.categoryId)} {...register("categoryId")}>
                  <option value="">Sin categoría</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </Select>
              </Field>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" className="size-4 accent-primary" {...register("active")} />
                Visible en la tienda
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" className="size-4 accent-primary" {...register("featured")} />
                Destacado en la home
              </label>
            </div>
          </Card>
          <Button type="submit" size="lg" loading={formState.isSubmitting}>
            {product ? "Guardar cambios" : "Crear producto"}
          </Button>
        </div>
      </div>
    </form>
  );
}
