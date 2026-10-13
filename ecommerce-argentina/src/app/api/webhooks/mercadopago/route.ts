import { revalidateTag } from "next/cache";
import type { NextRequest } from "next/server";
import { z } from "zod";
import { CATALOG_TAG } from "@/lib/catalog/data";
import { canCreateOrders, isMercadoPagoConfigured } from "@/lib/env.server";
import { syncPayment, verifyWebhookSignature } from "@/lib/payments/mercadopago";

const notificationSchema = z.object({
  type: z.string().min(1),
  dataId: z.string().regex(/^[\w-]{1,64}$/),
});

/**
 * Webhook de Mercado Pago (Tu aplicación → Webhooks → evento "Pagos").
 * Respuestas: 200 = procesado o ignorado, 401 = firma inválida, 500 = reintentar.
 */
export async function POST(request: NextRequest) {
  if (!isMercadoPagoConfigured || !canCreateOrders) {
    return Response.json({ error: "Tienda sin configurar" }, { status: 503 });
  }

  const url = request.nextUrl;
  const body = (await request.json().catch(() => null)) as { type?: unknown; data?: { id?: unknown } } | null;
  const parsed = notificationSchema.safeParse({
    type: url.searchParams.get("type") ?? body?.type,
    dataId: url.searchParams.get("data.id") ?? (body?.data?.id != null ? String(body.data.id) : undefined),
  });
  if (!parsed.success) return Response.json({ error: "Notificación inválida" }, { status: 400 });

  // Solo nos interesan pagos (merchant_order, etc. se ignoran).
  if (parsed.data.type !== "payment") return Response.json({ ignored: true });

  const signature = verifyWebhookSignature({
    signature: request.headers.get("x-signature"),
    requestId: request.headers.get("x-request-id"),
    dataId: url.searchParams.get("data.id"),
  });
  if (!signature.ok) {
    console.warn("[webhook mercadopago] firma inválida:", signature.reason);
    return Response.json({ error: "Firma inválida" }, { status: 401 });
  }

  try {
    const result = await syncPayment(parsed.data.dataId);
    if (!result) return Response.json({ ignored: true });

    if (result.newlyPaid) {
      // Cambió el stock: refrescar el catálogo cacheado.
      revalidateTag(CATALOG_TAG, "max");
    }
    return Response.json({ ok: true, status: result.paymentStatus });
  } catch (error) {
    console.error("[webhook mercadopago]", error);
    // 500 → Mercado Pago reintenta más tarde.
    return Response.json({ error: "Error procesando el pago" }, { status: 500 });
  }
}
