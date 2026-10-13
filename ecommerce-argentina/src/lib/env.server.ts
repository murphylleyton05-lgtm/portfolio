import "server-only";
import { z } from "zod";
import { isSupabaseConfigured } from "@/lib/env";

const optionalSecret = z.preprocess(
  (value) => (typeof value === "string" && value.trim() === "" ? undefined : value),
  z.string().min(10).optional(),
);

const serverSchema = z.object({
  supabaseSecretKey: optionalSecret,
  mercadoPagoAccessToken: optionalSecret,
  mercadoPagoWebhookSecret: optionalSecret,
  resendApiKey: optionalSecret,
  emailFrom: z.string().min(3).default("Tienda <onboarding@resend.dev>"),
});

const parsed = serverSchema.safeParse({
  supabaseSecretKey: process.env.SUPABASE_SECRET_KEY,
  mercadoPagoAccessToken: process.env.MERCADOPAGO_ACCESS_TOKEN,
  mercadoPagoWebhookSecret: process.env.MERCADOPAGO_WEBHOOK_SECRET,
  resendApiKey: process.env.RESEND_API_KEY,
  emailFrom: process.env.EMAIL_FROM || undefined,
});

if (!parsed.success) {
  throw new Error(`Variables de entorno inválidas:\n${z.prettifyError(parsed.error)}`);
}

export const serverEnv = parsed.data;

/** Se pueden crear pedidos: hay base de datos con clave secreta. */
export const canCreateOrders = isSupabaseConfigured && Boolean(serverEnv.supabaseSecretKey);
export const isMercadoPagoConfigured = Boolean(serverEnv.mercadoPagoAccessToken);
export const isResendConfigured = Boolean(serverEnv.resendApiKey);
