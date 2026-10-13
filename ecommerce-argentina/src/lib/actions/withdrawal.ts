"use server";

import { randomBytes } from "node:crypto";
import { z } from "zod";
import { siteConfig } from "@site-config";
import { canCreateOrders } from "@/lib/env.server";
import { escapeHtml } from "@/lib/email/templates";
import { sendEmail } from "@/lib/email/send";
import { createServiceClient } from "@/lib/supabase/admin";

const withdrawalSchema = z.object({
  orderNumber: z.coerce.number({ error: "Ingresá el número de pedido" }).int().min(1, "Número inválido").max(1e12),
  email: z.string().trim().toLowerCase().max(120).pipe(z.email("Email inválido")),
  name: z.string().trim().min(3, "Ingresá tu nombre").max(100),
  reason: z.string().trim().max(1000, "Máximo 1000 caracteres").optional(),
});

export type WithdrawalState = {
  ok?: boolean;
  code?: string;
  error?: string;
  fieldErrors?: Partial<Record<"orderNumber" | "email" | "name" | "reason", string>>;
};

/**
 * Botón de arrepentimiento (Res. 424/2020): registra la solicitud, avisa a la
 * tienda y le manda al cliente un código de constancia.
 */
export async function requestWithdrawal(_prev: WithdrawalState, formData: FormData): Promise<WithdrawalState> {
  const parsed = withdrawalSchema.safeParse({
    orderNumber: formData.get("orderNumber"),
    email: formData.get("email"),
    name: formData.get("name"),
    reason: formData.get("reason") || undefined,
  });
  if (!parsed.success) {
    const fieldErrors: WithdrawalState["fieldErrors"] = {};
    for (const issue of parsed.error.issues) {
      fieldErrors[issue.path[0] as keyof NonNullable<WithdrawalState["fieldErrors"]>] ??= issue.message;
    }
    return { error: "Revisá los datos.", fieldErrors };
  }
  const { orderNumber, email, name, reason } = parsed.data;

  if (!canCreateOrders) {
    return { error: `La tienda está en modo demo. Escribinos a ${siteConfig.contact.email}.` };
  }
  // El pedido tiene que existir y ser de ese email (evita usar el formulario para mandar spam).
  const { data: order } = await createServiceClient()
    .from("orders")
    .select("id")
    .eq("number", orderNumber)
    .eq("customer_email", email)
    .maybeSingle();
  if (!order) return { error: "No encontramos un pedido con ese número y email.", fieldErrors: {} };

  const code = `ARR-${orderNumber}-${randomBytes(3).toString("hex").toUpperCase()}`;
  const details = `Pedido #${orderNumber}\nNombre: ${name}\nEmail: ${email}\nMotivo: ${reason ?? "(sin motivo)"}\nCódigo: ${code}`;

  await sendEmail({
    to: siteConfig.contact.email,
    subject: `Botón de arrepentimiento: pedido #${orderNumber}`,
    text: details,
    html: `<p><strong>Solicitud de arrepentimiento</strong></p><pre style="font-family:inherit">${escapeHtml(details)}</pre>`,
  });
  const sent = await sendEmail({
    to: email,
    subject: `Recibimos tu solicitud de arrepentimiento (${code})`,
    text: `Hola ${name}:\n\nRecibimos tu solicitud para revocar la compra del pedido #${orderNumber}. Tu código de constancia es ${code}.\nTe vamos a contactar para coordinar la devolución.\n\n${siteConfig.name}`,
    html: `<p>Hola ${escapeHtml(name)}:</p><p>Recibimos tu solicitud para revocar la compra del pedido <strong>#${orderNumber}</strong>.</p><p>Tu código de constancia es <strong>${code}</strong>. Te vamos a contactar para coordinar la devolución.</p><p>${escapeHtml(siteConfig.name)}</p>`,
  });
  if (!sent.ok) return { error: "No pudimos registrar la solicitud. Escribinos a " + siteConfig.contact.email };
  return { ok: true, code };
}
