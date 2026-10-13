import "server-only";
import MercadoPagoConfig, { MPNotFoundError, Payment, Preference, WebhookSignatureValidator } from "mercadopago";
import type { PreferenceRequest } from "mercadopago/dist/clients/preference/commonTypes";
import { after } from "next/server";
import { z } from "zod";
import { siteConfig } from "@site-config";
import { sendOrderEmails } from "@/lib/email/orders";
import { absoluteUrl, publicEnv } from "@/lib/env";
import { isMercadoPagoConfigured, serverEnv } from "@/lib/env.server";
import { orderPath, type CreatedOrder } from "@/lib/orders/create";
import type { OrderWithItems } from "@/lib/orders/queries";
import { createServiceClient } from "@/lib/supabase/admin";

function mercadoPago() {
  if (!isMercadoPagoConfigured) throw new Error("Falta MERCADOPAGO_ACCESS_TOKEN.");
  return new MercadoPagoConfig({ accessToken: serverEnv.mercadoPagoAccessToken!, options: { timeout: 10_000 } });
}

/** Mercado Pago solo acepta webhooks y auto_return con URLs públicas https. */
const isPublicSite = () => publicEnv.siteUrl.startsWith("https://");

function splitName(fullName: string) {
  const [name, ...rest] = fullName.trim().split(/\s+/);
  return { name, surname: rest.join(" ") || undefined };
}

export type PreferenceInput = {
  id: string;
  accessToken: string;
  number: number;
  customer: { name: string; email: string; dni?: string | null };
  shippingCost: number;
  items: Array<{ id: string; title: string; quantity: number; unitPrice: number; image: string | null }>;
};

/** Arma los datos de la preferencia a partir de un pedido recién creado. */
export function preferenceInputFromOrder(order: CreatedOrder): PreferenceInput {
  return {
    id: order.id,
    accessToken: order.accessToken,
    number: order.number,
    customer: { name: order.form.name, email: order.form.email, dni: order.form.dni },
    shippingCost: order.shippingCost,
    items: order.lines.map((line) => ({
      id: line.variantId,
      title: line.variantName === "Único" ? line.name : `${line.name} (${line.variantName})`,
      quantity: line.quantity,
      unitPrice: line.price,
      image: line.image,
    })),
  };
}

/** Arma los datos de la preferencia a partir de un pedido guardado (reintento de pago). */
export function preferenceInputFromStoredOrder(order: OrderWithItems): PreferenceInput {
  return {
    id: order.id,
    accessToken: order.access_token,
    number: order.number,
    customer: { name: order.customer_name, email: order.customer_email, dni: order.customer_dni },
    shippingCost: Number(order.shipping_cost),
    items: order.items.map((item) => ({
      id: item.variant_id ?? item.id,
      title: item.variant_name === "Único" ? item.product_name : `${item.product_name} (${item.variant_name})`,
      quantity: item.quantity,
      unitPrice: Number(item.unit_price),
      image: item.image,
    })),
  };
}

/** Crea la preferencia de Checkout Pro, la guarda en el pedido y devuelve la URL de pago. */
export async function createPreference(order: PreferenceInput): Promise<{ id: string; initPoint: string }> {
  const backUrl = absoluteUrl(orderPath(order));
  const payer = splitName(order.customer.name);

  const items: PreferenceRequest["items"] = order.items.map((item) => {
    const picture = item.image ? absoluteUrl(item.image) : undefined;
    return {
      id: item.id,
      title: item.title,
      quantity: item.quantity,
      unit_price: item.unitPrice,
      currency_id: siteConfig.currency,
      // MP no muestra SVG; solo mandamos fotos reales.
      picture_url: picture && picture.startsWith("https://") && !picture.endsWith(".svg") ? picture : undefined,
    };
  });
  if (order.shippingCost > 0) {
    items.push({
      id: "envio",
      title: "Envío",
      quantity: 1,
      unit_price: order.shippingCost,
      currency_id: siteConfig.currency,
    });
  }

  const body: PreferenceRequest = {
    items,
    payer: {
      name: payer.name,
      surname: payer.surname,
      email: order.customer.email,
      ...(order.customer.dni ? { identification: { type: "DNI", number: order.customer.dni } } : {}),
    },
    external_reference: order.id,
    back_urls: { success: backUrl, pending: backUrl, failure: backUrl },
    payment_methods: { installments: siteConfig.payments.maxInstallments },
    statement_descriptor: siteConfig.payments.statementDescriptor.slice(0, 13),
    metadata: { order_id: order.id, order_number: order.number },
    ...(isPublicSite()
      ? {
          auto_return: "approved",
          // source_news=webhooks evita recibir también las notificaciones IPN (duplicadas).
          notification_url: absoluteUrl("/api/webhooks/mercadopago?source_news=webhooks"),
        }
      : {}),
  };

  const preference = await new Preference(mercadoPago()).create({ body });

  // Con credenciales TEST-… se usa el checkout de prueba.
  const initPoint = serverEnv.mercadoPagoAccessToken!.startsWith("TEST-")
    ? (preference.sandbox_init_point ?? preference.init_point)
    : preference.init_point;
  if (!preference.id || !initPoint) throw new Error("Mercado Pago no devolvió la URL de pago.");

  await createServiceClient()
    .from("orders")
    .update({ mp_preference_id: preference.id, mp_init_point: initPoint })
    .eq("id", order.id);

  return { id: preference.id, initPoint };
}

export type SyncResult = {
  orderId: string;
  paymentStatus: string;
  /** true solo la primera vez que el pedido pasa a pagado (para mandar el email una vez). */
  newlyPaid: boolean;
};

/**
 * Consulta el pago en la API de Mercado Pago (la única fuente confiable) y
 * actualiza el pedido. Idempotente: se puede llamar desde el webhook y desde la
 * página de vuelta sin descontar stock dos veces.
 */
export async function syncPayment(paymentId: string): Promise<SyncResult | null> {
  let payment: Awaited<ReturnType<Payment["get"]>>;
  try {
    payment = await new Payment(mercadoPago()).get({ id: paymentId });
  } catch (error) {
    // Pago inexistente (ej. la notificación de prueba del panel de MP).
    if (error instanceof MPNotFoundError) return null;
    throw error;
  }
  const orderId = z.uuid().safeParse(payment.external_reference);
  if (!orderId.success || payment.id === undefined) return null;

  const supabase = createServiceClient();
  const { data: order, error } = await supabase.from("orders").select("id, total").eq("id", orderId.data).maybeSingle();
  if (error) throw new Error(`No se pudo leer el pedido: ${error.message}`);
  if (!order) return null;

  let status = payment.status ?? "unknown";
  // Defensa extra: un pago "aprobado" por menos del total o en otra moneda no confirma el pedido.
  if (
    status === "approved" &&
    (payment.currency_id !== siteConfig.currency || (payment.transaction_amount ?? 0) + 0.01 < Number(order.total))
  ) {
    console.error("[mercadopago] Monto o moneda no coinciden", {
      orderId: order.id,
      paymentId: payment.id,
      amount: payment.transaction_amount,
      currency: payment.currency_id,
      expected: order.total,
    });
    status = "amount_mismatch";
  }

  const { data: newlyPaid, error: rpcError } = await supabase.rpc("confirm_order_payment", {
    p_order_id: order.id,
    p_payment_id: String(payment.id),
    p_payment_status: status,
    p_payment_status_detail: payment.status_detail ?? null,
  });
  if (rpcError) throw new Error(`No se pudo actualizar el pedido: ${rpcError.message}`);

  // Email de confirmación después de responder (se manda una sola vez por pedido).
  if (status === "approved") after(() => sendOrderEmails(order.id));

  return { orderId: order.id, paymentStatus: status, newlyPaid: Boolean(newlyPaid) };
}

/** Busca pagos de un pedido (por si el webhook no llegó) y sincroniza el más relevante. */
export async function syncPaymentsForOrder(orderId: string): Promise<SyncResult | null> {
  const search = await new Payment(mercadoPago()).search({
    options: { external_reference: orderId, sort: "date_created", criteria: "desc" },
  });
  const results = search.results ?? [];
  const best = results.find((payment) => payment.status === "approved") ?? results[0];
  return best?.id ? syncPayment(String(best.id)) : null;
}

/**
 * Valida la firma `x-signature` de un webhook. Si no hay clave secreta
 * configurada, no se valida (el pago igual se verifica contra la API).
 */
export function verifyWebhookSignature(input: { signature: string | null; requestId: string | null; dataId: string | null }) {
  if (!serverEnv.mercadoPagoWebhookSecret) return { ok: true as const, verified: false };
  try {
    WebhookSignatureValidator.validate({
      xSignature: input.signature,
      xRequestId: input.requestId,
      // MP firma el data.id en minúscula cuando es alfanumérico.
      dataId: input.dataId?.toLowerCase() ?? null,
      secret: serverEnv.mercadoPagoWebhookSecret,
      // Sin ventana de tiempo: los reintentos de MP pueden llegar tarde y un
      // "replay" es inofensivo (el pago se vuelve a consultar en la API).
    });
    return { ok: true as const, verified: true };
  } catch (error) {
    return { ok: false as const, reason: error instanceof Error ? error.message : "firma inválida" };
  }
}
