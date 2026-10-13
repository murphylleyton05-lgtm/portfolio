"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useForm, useWatch, type FieldErrors } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Lock } from "lucide-react";
import { siteConfig } from "@site-config";
import { Alert } from "@/components/ui/alert";
import { Button, buttonClasses } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { Skeleton } from "@/components/ui/skeleton";
import { placeOrder } from "@/lib/actions/checkout";
import { PROVINCES, parsePostalCode } from "@/lib/argentina";
import { useCart } from "@/lib/cart/store";
import { cartSubtotal } from "@/lib/cart/types";
import { useCartSync } from "@/lib/cart/use-cart-sync";
import {
  checkoutFormSchema,
  type CheckoutFormInput,
  type CheckoutFormValues,
  type ShippingFormInput,
} from "@/lib/checkout/schema";
import { quoteShipping } from "@/lib/shipping";
import { formatPrice } from "@/lib/utils";

type Props = {
  /** false en modo demo (sin Supabase): se muestra el formulario pero no se puede enviar. */
  ordersEnabled: boolean;
  /** Texto del botón final (cambia si hay Mercado Pago). */
  submitLabel: string;
};

export function CheckoutForm({ ordersEnabled, submitLabel }: Props) {
  const { hydrated, syncing, notices } = useCartSync();
  const items = useCart((state) => state.items);
  const clearCart = useCart((state) => state.clear);
  const [serverError, setServerError] = useState<{ message: string; problems?: string[] } | null>(null);

  const { register, handleSubmit, setError, formState, control } = useForm<CheckoutFormInput, unknown, CheckoutFormValues>({
    resolver: zodResolver(checkoutFormSchema),
    mode: "onTouched",
    defaultValues: {
      deliveryMethod: "shipping",
      email: "",
      name: "",
      phone: "",
      dni: "",
      notes: "",
      address: { street: "", number: "", apartment: "", city: "", province: "" as never, postalCode: "" },
    },
  });
  const errors = formState.errors as FieldErrors<ShippingFormInput>;
  const deliveryMethod = useWatch({ control, name: "deliveryMethod" });
  const postalCode = useWatch({ control, name: "address.postalCode" }) as string | undefined;

  if (!hydrated) return <CheckoutSkeleton />;

  if (!items.length) {
    return (
      <div className="flex flex-col items-start gap-4 rounded-2xl border border-dashed border-border p-8">
        <p className="text-lg font-medium">No hay productos en tu carrito.</p>
        <Link href="/productos" className={buttonClasses("primary")}>
          Ver productos
        </Link>
      </div>
    );
  }

  const subtotal = cartSubtotal(items);
  const validPostalCode = postalCode ? parsePostalCode(postalCode) !== null : false;
  const quote =
    deliveryMethod === "pickup" || validPostalCode
      ? quoteShipping({ method: deliveryMethod, postalCode, subtotal })
      : null;
  const total = subtotal + (quote?.cost ?? 0);

  async function onSubmit(values: CheckoutFormValues) {
    setServerError(null);
    const result = await placeOrder({
      form: values,
      items: useCart.getState().items.map(({ variantId, quantity }) => ({ variantId, quantity })),
    });
    if (!result.ok) {
      for (const [name, message] of Object.entries(result.fieldErrors ?? {})) {
        setError(name as keyof CheckoutFormInput, { message });
      }
      setServerError({ message: result.error, problems: result.problems });
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    clearCart();
    window.location.assign(result.redirectUrl);
  }

  /** Mensaje de error para un campo (soporta rutas como "address.city"). */
  const err = (name: string) =>
    (
      name.split(".").reduce<unknown>((acc, key) => (acc as Record<string, unknown> | undefined)?.[key], errors) as
        | { message?: string }
        | undefined
    )?.message;

  /** id + atributos aria que conectan el control con su mensaje de error. */
  const aria = (name: string) => ({
    id: name,
    "aria-invalid": err(name) ? true : undefined,
    "aria-describedby": err(name) ? `${name}-error` : undefined,
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="grid gap-8 lg:grid-cols-[1fr_24rem]">
      <div className="flex flex-col gap-8">
        {!ordersEnabled && (
          <Alert tone="warning" title="Tienda en modo demo">
            Podés probar el formulario, pero para recibir pedidos hay que configurar Supabase y Mercado Pago (ver README).
          </Alert>
        )}
        {serverError && (
          <Alert tone="error" title={serverError.message}>
            {serverError.problems?.length ? (
              <ul className="list-disc pl-4">
                {serverError.problems.map((problem) => (
                  <li key={problem}>{problem}</li>
                ))}
              </ul>
            ) : null}
            {serverError.problems?.length ? (
              <Link href="/carrito" className="mt-2 inline-block underline">
                Revisar carrito
              </Link>
            ) : null}
          </Alert>
        )}
        {notices.length > 0 && (
          <Alert tone="warning" title="Actualizamos tu carrito">
            <ul className="list-disc pl-4">
              {notices.map((notice) => (
                <li key={notice}>{notice}</li>
              ))}
            </ul>
          </Alert>
        )}

        <fieldset className="flex flex-col gap-4">
          <legend className="mb-2 text-lg font-semibold">Tus datos</legend>
          <Field label="Email" id="email" error={err("email")}>
            <Input {...aria("email")} type="email" autoComplete="email" inputMode="email" {...register("email")} />
          </Field>
          <Field label="Nombre y apellido" id="name" error={err("name")}>
            <Input {...aria("name")} autoComplete="name" {...register("name")} />
          </Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Teléfono" hint="Para coordinar la entrega." id="phone" error={err("phone")}>
              <Input {...aria("phone")} type="tel" autoComplete="tel" inputMode="tel" placeholder="11 2345-6789" {...register("phone")} />
            </Field>
            <Field label="DNI (opcional)" id="dni" error={err("dni")}>
              <Input {...aria("dni")} inputMode="numeric" placeholder="Sin puntos" {...register("dni")} />
            </Field>
          </div>
        </fieldset>

        <fieldset className="flex flex-col gap-4">
          <legend className="mb-2 text-lg font-semibold">Entrega</legend>
          <input type="hidden" value="shipping" {...register("deliveryMethod")} />
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Calle" className="sm:col-span-2" id="address.street" error={err("address.street")}>
              <Input {...aria("address.street")} autoComplete="address-line1" {...register("address.street")} />
            </Field>
            <Field label="Número" id="address.number" error={err("address.number")}>
              <Input {...aria("address.number")} inputMode="numeric" {...register("address.number")} />
            </Field>
            <Field label="Piso / depto (opcional)" id="address.apartment" error={err("address.apartment")}>
              <Input {...aria("address.apartment")} autoComplete="address-line2" {...register("address.apartment")} />
            </Field>
            <Field label="Localidad" id="address.city" error={err("address.city")}>
              <Input {...aria("address.city")} autoComplete="address-level2" {...register("address.city")} />
            </Field>
            <Field label="Código postal" id="address.postalCode" error={err("address.postalCode")}>
              <Input {...aria("address.postalCode")} autoComplete="postal-code" placeholder="1425 o C1425ABC" {...register("address.postalCode")} />
            </Field>
            <Field label="Provincia" className="sm:col-span-2" id="address.province" error={err("address.province")}>
              <Select
                {...aria("address.province")}
                autoComplete="address-level1"
                {...register("address.province")}
              >
                <option value="">Elegí una provincia</option>
                {PROVINCES.map((province) => (
                  <option key={province} value={province}>
                    {province}
                  </option>
                ))}
              </Select>
            </Field>
          </div>
        </fieldset>

        <Field label="Notas para el pedido (opcional)" id="notes" error={err("notes")}>
          <Textarea
            {...aria("notes")}
            maxLength={500}
            placeholder="Ej: tocar timbre B, horario de entrega…"
            {...register("notes")}
          />
        </Field>
      </div>

      <aside className="flex h-fit flex-col gap-4 rounded-2xl bg-muted/60 p-6 lg:sticky lg:top-24">
        <h2 className="font-semibold">Tu pedido</h2>
        <ul className="flex flex-col gap-3">
          {items.map((item) => (
            <li key={item.variantId} className="flex items-center gap-3 text-sm">
              <div className="relative aspect-[4/5] w-12 shrink-0 overflow-hidden rounded-md bg-muted">
                {item.image && <Image src={item.image} alt="" fill sizes="48px" className="object-cover" />}
                <span className="absolute -top-1 -right-1 flex size-5 items-center justify-center rounded-full bg-primary text-[11px] text-primary-foreground">
                  {item.quantity}
                </span>
              </div>
              <div className="flex-1">
                <p className="font-medium">{item.name}</p>
                {item.variantName !== "Único" && <p className="text-muted-foreground">{item.variantName}</p>}
              </div>
              <p className="tabular-nums">{formatPrice(item.price * item.quantity)}</p>
            </li>
          ))}
        </ul>
        <dl className="flex flex-col gap-2 border-t border-border pt-4 text-sm">
          <div className="flex justify-between">
            <dt>Subtotal</dt>
            <dd className="tabular-nums">{formatPrice(subtotal)}</dd>
          </div>
          <div className="flex justify-between">
            <dt>Envío{quote ? ` · ${quote.zoneName}` : ""}</dt>
            <dd className="tabular-nums">{quote ? (quote.cost ? formatPrice(quote.cost) : "Gratis") : "Ingresá tu CP"}</dd>
          </div>
          {quote?.eta && <p className="text-xs text-muted-foreground">Llega en {quote.eta}.</p>}
          <div className="flex justify-between border-t border-border pt-2 text-base font-semibold">
            <dt>Total</dt>
            <dd className="tabular-nums">{formatPrice(total)}</dd>
          </div>
        </dl>
        <Button type="submit" size="lg" loading={formState.isSubmitting} disabled={!ordersEnabled || syncing}>
          {formState.isSubmitting ? "Procesando…" : submitLabel}
        </Button>
        <p className="flex items-center justify-center gap-1.5 text-xs text-muted-foreground">
          <Lock className="size-3.5" aria-hidden /> Pago seguro · {siteConfig.name}
        </p>
      </aside>
    </form>
  );
}

function CheckoutSkeleton() {
  return (
    <div role="status" aria-label="Cargando checkout" className="grid gap-8 lg:grid-cols-[1fr_24rem]">
      <div className="flex flex-col gap-4">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-11" />
        <Skeleton className="h-11" />
        <Skeleton className="h-11" />
      </div>
      <Skeleton className="h-72 rounded-2xl" />
    </div>
  );
}
