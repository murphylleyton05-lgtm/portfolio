"use client";

import Image from "next/image";
import Link from "next/link";
import { Minus, Plus, ShoppingBag, Trash2 } from "lucide-react";
import { siteConfig } from "@site-config";
import { Alert } from "@/components/ui/alert";
import { buttonClasses } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useCart } from "@/lib/cart/store";
import { MAX_QUANTITY_PER_ITEM, cartSubtotal } from "@/lib/cart/types";
import { useCartSync } from "@/lib/cart/use-cart-sync";
import { formatPrice } from "@/lib/utils";

export function CartView() {
  const { hydrated, syncing, notices } = useCartSync();
  const items = useCart((state) => state.items);
  const setQuantity = useCart((state) => state.setQuantity);
  const remove = useCart((state) => state.remove);

  if (!hydrated) return <CartSkeleton />;

  if (!items.length) {
    return (
      <div className="flex flex-col items-center gap-4 rounded-2xl border border-dashed border-border px-6 py-16 text-center">
        <ShoppingBag className="size-10 text-muted-foreground" aria-hidden />
        <p className="text-lg font-medium">Tu carrito está vacío</p>
        {notices.length > 0 && (
          <Alert tone="warning" className="text-left">
            <ul className="list-disc pl-4">
              {notices.map((notice) => (
                <li key={notice}>{notice}</li>
              ))}
            </ul>
          </Alert>
        )}
        <Link href="/productos" className={buttonClasses("primary")}>
          Ver productos
        </Link>
      </div>
    );
  }

  const subtotal = cartSubtotal(items);
  const threshold = siteConfig.shipping.enabled ? siteConfig.shipping.freeShippingThreshold : null;
  const missingForFree = threshold ? threshold - subtotal : 0;

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_22rem]">
      <section aria-label="Productos en el carrito" className="flex flex-col gap-4">
        {notices.length > 0 && (
          <Alert tone="warning" title="Actualizamos tu carrito">
            <ul className="list-disc pl-4">
              {notices.map((notice) => (
                <li key={notice}>{notice}</li>
              ))}
            </ul>
          </Alert>
        )}
        <ul className="divide-y divide-border border-y border-border">
          {items.map((item) => {
            const max = Math.min(item.stock, MAX_QUANTITY_PER_ITEM);
            return (
              <li key={item.variantId} className="flex gap-4 py-4">
                <Link href={`/productos/${item.slug}`} className="relative aspect-[4/5] w-20 shrink-0 overflow-hidden rounded-lg bg-muted sm:w-24">
                  {item.image && <Image src={item.image} alt={item.name} fill sizes="96px" className="object-cover" />}
                </Link>
                <div className="flex flex-1 flex-col gap-2">
                  <div className="flex justify-between gap-3">
                    <div>
                      <Link href={`/productos/${item.slug}`} className="text-sm font-medium hover:underline">
                        {item.name}
                      </Link>
                      {item.variantName !== "Único" && <p className="text-sm text-muted-foreground">{item.variantName}</p>}
                    </div>
                    <p className="text-sm font-semibold tabular-nums">{formatPrice(item.price * item.quantity)}</p>
                  </div>
                  <div className="mt-auto flex items-center justify-between gap-3">
                    <div className="flex h-9 items-center rounded-lg border border-border">
                      <button
                        type="button"
                        className="inline-flex size-9 items-center justify-center disabled:opacity-40"
                        onClick={() => setQuantity(item.variantId, item.quantity - 1)}
                        disabled={item.quantity <= 1}
                        aria-label={`Restar uno de ${item.name}`}
                      >
                        <Minus className="size-3.5" aria-hidden />
                      </button>
                      <span className="w-8 text-center text-sm tabular-nums" aria-label="Cantidad">
                        {item.quantity}
                      </span>
                      <button
                        type="button"
                        className="inline-flex size-9 items-center justify-center disabled:opacity-40"
                        onClick={() => setQuantity(item.variantId, item.quantity + 1)}
                        disabled={item.quantity >= max}
                        aria-label={`Sumar uno de ${item.name}`}
                      >
                        <Plus className="size-3.5" aria-hidden />
                      </button>
                    </div>
                    <button
                      type="button"
                      onClick={() => remove(item.variantId)}
                      className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-red-600"
                    >
                      <Trash2 className="size-4" aria-hidden /> Quitar
                    </button>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
        <Link href="/productos" className="text-sm underline underline-offset-4">
          Seguir comprando
        </Link>
      </section>

      <aside className="flex h-fit flex-col gap-4 rounded-2xl bg-muted/60 p-6 lg:sticky lg:top-24">
        <h2 className="font-semibold">Resumen</h2>
        <dl className="flex flex-col gap-2 text-sm">
          <div className="flex justify-between">
            <dt>Subtotal</dt>
            <dd className="font-medium tabular-nums">{formatPrice(subtotal)}</dd>
          </div>
          <div className="flex justify-between text-muted-foreground">
            <dt>Envío</dt>
            <dd>Se calcula en el checkout</dd>
          </div>
        </dl>
        {threshold !== null && (
          <p className="text-sm text-muted-foreground">
            {missingForFree > 0
              ? `Te faltan ${formatPrice(missingForFree)} para el envío gratis.`
              : "¡Tenés envío gratis!"}
          </p>
        )}
        <Link
          href="/checkout"
          aria-disabled={syncing}
          className={buttonClasses("primary", "lg", syncing ? "pointer-events-none opacity-60" : "")}
        >
          {syncing ? "Verificando stock…" : "Iniciar compra"}
        </Link>
      </aside>
    </div>
  );
}

function CartSkeleton() {
  return (
    <div role="status" aria-label="Cargando carrito" className="grid gap-8 lg:grid-cols-[1fr_22rem]">
      <div className="flex flex-col gap-4">
        {[0, 1].map((key) => (
          <div key={key} className="flex gap-4">
            <Skeleton className="aspect-[4/5] w-20" />
            <div className="flex flex-1 flex-col gap-2">
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-4 w-1/4" />
            </div>
          </div>
        ))}
      </div>
      <Skeleton className="h-56 rounded-2xl" />
    </div>
  );
}
