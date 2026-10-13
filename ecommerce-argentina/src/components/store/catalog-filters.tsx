import Form from "next/form";
import Link from "next/link";
import { SlidersHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/field";
import { SORT_OPTIONS, catalogHref, type CatalogQuery } from "@/lib/catalog/query";
import type { CatalogCategory } from "@/lib/catalog/types";
import { AutoSubmitSelect } from "./auto-submit-select";

type Props = { query: CatalogQuery; categories: CatalogCategory[] };

function hasActiveFilters(query: CatalogQuery) {
  return Boolean(query.q || query.categoria || query.min !== undefined || query.max !== undefined || query.stock);
}

/**
 * Filtros como formularios GET: funcionan sin JavaScript y con JS navegan sin
 * recargar. Mobile y desktop usan formularios separados para no duplicar campos.
 */
export function CatalogFilters({ query, categories }: Props) {
  return (
    <>
      <details className="lg:hidden">
        <summary className="inline-flex h-11 cursor-pointer list-none items-center gap-2 rounded-lg border border-border px-4 text-sm font-medium [&::-webkit-details-marker]:hidden">
          <SlidersHorizontal className="size-4" aria-hidden /> Filtros
          {hasActiveFilters(query) && (
            <span className="size-2 rounded-full bg-accent" aria-label="(hay filtros activos)" />
          )}
        </summary>
        <div className="mt-4 rounded-xl border border-border p-4">
          <FiltersForm query={query} categories={categories} idPrefix="m" />
        </div>
      </details>
      <div className="hidden lg:block">
        <FiltersForm query={query} categories={categories} idPrefix="d" />
      </div>
    </>
  );
}

function FiltersForm({ query, categories, idPrefix }: Props & { idPrefix: string }) {
  const id = (name: string) => `${idPrefix}-${name}`;
  return (
    <Form action="/productos" className="flex flex-col gap-4">
      <input type="hidden" name="orden" value={query.orden} />
      <div className="flex flex-col gap-1.5">
        <label htmlFor={id("q")} className="text-sm font-medium">
          Buscar
        </label>
        <Input id={id("q")} name="q" type="search" defaultValue={query.q} maxLength={80} placeholder="Ej: buzo" />
      </div>
      <div className="flex flex-col gap-1.5">
        <label htmlFor={id("categoria")} className="text-sm font-medium">
          Categoría
        </label>
        <Select id={id("categoria")} name="categoria" defaultValue={query.categoria ?? ""}>
          <option value="">Todas</option>
          {categories.map((category) => (
            <option key={category.id} value={category.slug}>
              {category.name}
            </option>
          ))}
        </Select>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div className="flex flex-col gap-1.5">
          <label htmlFor={id("min")} className="text-sm font-medium">
            Precio mín.
          </label>
          <Input
            id={id("min")}
            name="min"
            type="number"
            inputMode="numeric"
            min={0}
            step={1}
            defaultValue={query.min}
            placeholder="$"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor={id("max")} className="text-sm font-medium">
            Precio máx.
          </label>
          <Input
            id={id("max")}
            name="max"
            type="number"
            inputMode="numeric"
            min={0}
            step={1}
            defaultValue={query.max}
            placeholder="$"
          />
        </div>
      </div>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          name="stock"
          value="1"
          defaultChecked={Boolean(query.stock)}
          className="size-4 accent-primary"
        />
        Solo con stock
      </label>
      <Button type="submit">Aplicar filtros</Button>
      {hasActiveFilters(query) && (
        <Link href={catalogHref({ orden: query.orden })} className="text-sm underline underline-offset-4">
          Limpiar filtros
        </Link>
      )}
    </Form>
  );
}

/** "Ordenar por": conserva los filtros actuales como campos ocultos. */
export function SortForm({ query }: { query: CatalogQuery }) {
  const keep = { q: query.q, categoria: query.categoria, min: query.min, max: query.max, stock: query.stock };
  return (
    <Form action="/productos" className="flex items-center gap-2">
      {Object.entries(keep).map(([name, value]) =>
        value === undefined ? null : <input key={name} type="hidden" name={name} value={String(value)} />,
      )}
      <label htmlFor="orden" className="text-sm whitespace-nowrap text-muted-foreground">
        Ordenar por
      </label>
      <AutoSubmitSelect id="orden" name="orden" defaultValue={query.orden} className="w-auto">
        {SORT_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </AutoSubmitSelect>
      <noscript>
        <Button type="submit" size="sm" variant="outline">
          Ordenar
        </Button>
      </noscript>
    </Form>
  );
}
