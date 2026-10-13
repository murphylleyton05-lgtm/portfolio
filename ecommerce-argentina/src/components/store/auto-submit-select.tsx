"use client";

import type { SelectHTMLAttributes } from "react";
import { Select } from "@/components/ui/field";

/** Select que envía su formulario al cambiar (ej. "Ordenar por"). */
export function AutoSubmitSelect(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <Select {...props} onChange={(event) => event.currentTarget.form?.requestSubmit()} />;
}
