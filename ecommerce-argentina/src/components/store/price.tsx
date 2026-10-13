import { cn, formatPrice } from "@/lib/utils";

export function Price({
  amount,
  compareAt,
  from,
  className,
  size = "md",
}: {
  amount: number;
  compareAt?: number | null;
  /** Muestra "Desde" (producto con variantes de distinto precio). */
  from?: boolean;
  className?: string;
  size?: "sm" | "md" | "lg";
}) {
  const onSale = compareAt != null && compareAt > amount;
  return (
    <p className={cn("flex flex-wrap items-baseline gap-x-2", className)}>
      {from && <span className="text-xs text-muted-foreground">Desde</span>}
      <span
        className={cn(
          "font-semibold tabular-nums",
          size === "sm" && "text-sm",
          size === "md" && "text-base",
          size === "lg" && "text-2xl",
          onSale && "text-accent",
        )}
      >
        {formatPrice(amount)}
      </span>
      {onSale && (
        <span className="text-sm text-muted-foreground tabular-nums line-through">
          <span className="sr-only">Antes: </span>
          {formatPrice(compareAt)}
        </span>
      )}
    </p>
  );
}

export function discountPercent(price: number, compareAt: number | null) {
  if (!compareAt || compareAt <= price) return 0;
  return Math.round((1 - price / compareAt) * 100);
}
