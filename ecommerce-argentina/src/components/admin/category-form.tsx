"use client";

import { useActionState, useEffect, useRef, useState } from "react";
import { saveCategory, type CategoryState } from "@/lib/actions/admin/categories";
import { slugify } from "@/lib/utils";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";

type Category = { id: string; name: string; slug: string; description: string; position: number };

export function CategoryForm({ category }: { category?: Category }) {
  const [state, action, pending] = useActionState<CategoryState, FormData>(saveCategory, {});
  const formRef = useRef<HTMLFormElement>(null);
  const [slug, setSlug] = useState(category?.slug ?? "");
  const [slugTouched, setSlugTouched] = useState(Boolean(category));
  const prefix = category?.id ?? "new";

  useEffect(() => {
    if (state.ok && !category) {
      formRef.current?.reset();
    }
  }, [state, category]);

  return (
    <form ref={formRef} action={action} className="grid gap-3 sm:grid-cols-[1fr_1fr_2fr_5rem_auto] sm:items-end">
      {category && <input type="hidden" name="id" value={category.id} />}
      <Field id={`${prefix}-name`} label="Nombre" error={state.fieldErrors?.name}>
        <Input
          id={`${prefix}-name`}
          name="name"
          defaultValue={category?.name}
          required
          onChange={(event) => !slugTouched && setSlug(slugify(event.target.value))}
        />
      </Field>
      <Field id={`${prefix}-slug`} label="Slug" error={state.fieldErrors?.slug}>
        <Input
          id={`${prefix}-slug`}
          name="slug"
          value={slug}
          required
          onChange={(event) => {
            setSlugTouched(true);
            setSlug(event.target.value);
          }}
        />
      </Field>
      <Field id={`${prefix}-description`} label="Descripción" error={state.fieldErrors?.description}>
        <Input id={`${prefix}-description`} name="description" defaultValue={category?.description} />
      </Field>
      <Field id={`${prefix}-position`} label="Orden" error={state.fieldErrors?.position}>
        <Input id={`${prefix}-position`} name="position" type="number" min={0} defaultValue={category?.position ?? 0} />
      </Field>
      <Button type="submit" loading={pending} variant={category ? "outline" : "primary"}>
        {category ? "Guardar" : "Crear"}
      </Button>
      {state.error && (
        <Alert tone="error" className="sm:col-span-5">
          {state.error}
        </Alert>
      )}
    </form>
  );
}
