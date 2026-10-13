import Form from "next/form";
import { Search } from "lucide-react";
import { cn } from "@/lib/utils";

/** Búsqueda: GET a /productos?q=… (funciona también sin JavaScript). */
export function SearchForm({
  className,
  defaultValue,
  id = "search",
}: {
  className?: string;
  defaultValue?: string;
  id?: string;
}) {
  return (
    <Form action="/productos" role="search" className={cn("relative", className)}>
      <label htmlFor={id} className="sr-only">
        Buscar productos
      </label>
      <Search
        className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
        aria-hidden
      />
      <input
        id={id}
        name="q"
        type="search"
        defaultValue={defaultValue}
        placeholder="Buscar productos…"
        maxLength={80}
        autoComplete="off"
        className="h-10 w-full rounded-lg border border-border bg-muted/60 pr-3 pl-9 text-sm outline-none transition focus:border-primary focus:bg-background"
      />
    </Form>
  );
}
