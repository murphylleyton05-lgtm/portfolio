"use client";

import { useState } from "react";
import Link from "next/link";
import { Check, Minus, Plus } from "lucide-react";
import { siteConfig } from "@site-config";
import { Button, buttonClasses } from "@/components/ui/button";
import { useCart } from "@/lib/cart/store";
import { MAX_QUANTITY_PER_ITEM } from "@/lib/cart/types";
import type { CatalogProduct } from "@/lib/catalog/types";
import { cn } from "@/lib/utils";
import { Price } from "./price";

type Props = {
  product: Pick<CatalogProduct, "id" | "slug" | "name" | "images" | "compareAtPrice" | "variants">;
};

export function AddToCart({ product }: Props) {
  const add = useCart((state) => state.add);
  const inCart = useCart((state) => state.items);
  const singleVariant = product.variants.length === 1;
  const firstAvailable = product.variants.find((variant) => variant.stock > 0) ?? product.variants[0];
  const [variantId, setVariantId] = useState<string | null>(singleVariant ? firstAvailable.id : null);
  const [quantity, setQuantity] = useState(1);
  const [added, setAdded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const variant = product.variants.find((v) => v.id === variantId) ?? null;
  const shownPrice = variant?.price ?? Math.min(...product.variants.map((v) => v.price));
  const alreadyInCart = variant ? (inCart.find((item) => item.variantId === variant.id)?.quantity ?? 0) : 0;
  const maxQuantity = variant ? Math.max(0, Math.min(variant.stock, MAX_QUANTITY_PER_ITEM) - alreadyInCart) : 0;
  const soldOut = product.variants.every((v) => v.stock <= 0);

  function handleAdd() {
    setError(null);
    if (!variant) {
      setError("Elegí una opción.");
      return;
    }
    if (maxQuantity <= 0) {
      setError(alreadyInCart ? "Ya tenés en el carrito todo el stock disponible." : "Sin stock.");
      return;
    }
    add(
      {
        variantId: variant.id,
        productId: product.id,
        slug: product.slug,
        name: product.name,
        variantName: variant.name,
        price: variant.price,
        image: product.images[0] ?? null,
        stock: variant.stock,
      },
      Math.min(quantity, maxQuantity),
    );
    setQuantity(1);
    setAdded(true);
  }

  return (
    <div className="flex flex-col gap-5">
      <Price
        amount={shownPrice}
        compareAt={product.compareAtPrice}
        from={!variant && new Set(product.variants.map((v) => v.price)).size > 1}
        size="lg"
      />
      {siteConfig.payments.installmentsBanner && (
        <p className="-mt-3 text-sm text-muted-foreground">{siteConfig.payments.installmentsBanner}</p>
      )}

      {!singleVariant && (
        <fieldset>
          <legend className="mb-2 text-sm font-medium">Opción{variant ? `: ${variant.name}` : ""}</legend>
          <div className="flex flex-wrap gap-2">
            {product.variants.map((v) => {
              const unavailable = v.stock <= 0;
              const selected = v.id === variantId;
              return (
                <button
                  key={v.id}
                  type="button"
                  aria-pressed={selected}
                  disabled={unavailable}
                  onClick={() => {
                    setVariantId(v.id);
                    setQuantity(1);
                    setAdded(false);
                    setError(null);
                  }}
                  className={cn(
                    "min-w-12 rounded-lg border px-3 py-2 text-sm transition",
                    selected
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-border hover:border-primary",
                    unavailable && "cursor-not-allowed text-muted-foreground line-through opacity-60",
                  )}
                >
                  {v.name}
                </button>
              );
            })}
          </div>
        </fieldset>
      )}

      <StockLabel stock={variant ? variant.stock : soldOut ? 0 : null} />

      <div className="flex gap-3">
        <div className="flex h-12 items-center rounded-lg border border-border">
          <button
            type="button"
            className="inline-flex size-11 items-center justify-center disabled:opacity-40"
            onClick={() => setQuantity((q) => Math.max(1, q - 1))}
            disabled={quantity <= 1}
            aria-label="Restar uno"
          >
            <Minus className="size-4" aria-hidden />
          </button>
          <output className="w-8 text-center text-sm tabular-nums" aria-live="polite" aria-label="Cantidad">
            {quantity}
          </output>
          <button
            type="button"
            className="inline-flex size-11 items-center justify-center disabled:opacity-40"
            onClick={() => setQuantity((q) => Math.min(q + 1, Math.max(1, maxQuantity)))}
            disabled={!variant || quantity >= maxQuantity}
            aria-label="Sumar uno"
          >
            <Plus className="size-4" aria-hidden />
          </button>
        </div>
        <Button size="lg" className="flex-1" onClick={handleAdd} disabled={soldOut}>
          {soldOut ? "Sin stock" : "Agregar al carrito"}
        </Button>
      </div>

      {error && (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}
      {added && !error && (
        <div
          role="status"
          className="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-900"
        >
          <span className="flex items-center gap-2">
            <Check className="size-4" aria-hidden /> Agregado al carrito
          </span>
          <Link href="/carrito" className={buttonClasses("primary", "sm")}>
            Ver carrito
          </Link>
        </div>
      )}
    </div>
  );
}

function StockLabel({ stock }: { stock: number | null }) {
  if (stock === null) return null;
  if (stock <= 0) return <p className="text-sm font-medium text-red-600">Sin stock</p>;
  if (stock <= siteConfig.catalog.lowStockThreshold) {
    return (
      <p className="text-sm font-medium text-amber-700">¡Últimas {stock === 1 ? "unidad" : `${stock} unidades`}!</p>
    );
  }
  return <p className="text-sm text-emerald-700">En stock</p>;
}
