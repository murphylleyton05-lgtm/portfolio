"use client";

import { useActionState } from "react";
import { updateStock, type StockState } from "@/lib/actions/admin/stock";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/field";

export function StockRowForm({ variantId, stock, label }: { variantId: string; stock: number; label: string }) {
  const [state, action, pending] = useActionState<StockState, FormData>(updateStock, {});
  return (
    <form action={action} className="flex items-center justify-end gap-2">
      <input type="hidden" name="variantId" value={variantId} />
      <label htmlFor={`stock-${variantId}`} className="sr-only">
        Stock de {label}
      </label>
      <Input
        id={`stock-${variantId}`}
        name="stock"
        type="number"
        inputMode="numeric"
        min={0}
        step={1}
        defaultValue={stock}
        key={stock}
        className="h-9 w-24 text-right"
        aria-invalid={state.error ? true : undefined}
      />
      <Button type="submit" size="sm" variant="outline" loading={pending}>
        Guardar
      </Button>
      <span className="w-16 text-xs text-emerald-700" aria-live="polite">
        {state.ok && !pending ? "Guardado" : ""}
      </span>
      {state.error && <span className="text-xs text-red-600">{state.error}</span>}
    </form>
  );
}
