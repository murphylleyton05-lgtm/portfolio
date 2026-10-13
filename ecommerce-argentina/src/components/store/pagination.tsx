import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { catalogHref, type CatalogQuery } from "@/lib/catalog/query";
import { cn } from "@/lib/utils";

export function Pagination({ query, page, pageCount }: { query: CatalogQuery; page: number; pageCount: number }) {
  if (pageCount <= 1) return null;
  const pages = Array.from({ length: pageCount }, (_, index) => index + 1);
  const linkClass = "inline-flex size-10 items-center justify-center rounded-lg border border-border text-sm";

  return (
    <nav aria-label="Paginación" className="mt-10 flex items-center justify-center gap-2">
      {page > 1 && (
        <Link href={catalogHref(query, { pagina: page - 1 })} className={linkClass} aria-label="Página anterior">
          <ChevronLeft className="size-4" aria-hidden />
        </Link>
      )}
      {pages.map((n) => (
        <Link
          key={n}
          href={catalogHref(query, { pagina: n })}
          aria-current={n === page ? "page" : undefined}
          className={cn(linkClass, n === page && "border-primary bg-primary text-primary-foreground")}
        >
          {n}
        </Link>
      ))}
      {page < pageCount && (
        <Link href={catalogHref(query, { pagina: page + 1 })} className={linkClass} aria-label="Página siguiente">
          <ChevronRight className="size-4" aria-hidden />
        </Link>
      )}
    </nav>
  );
}
