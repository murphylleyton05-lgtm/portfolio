import "server-only";
import { Resend } from "resend";
import { siteConfig } from "@site-config";
import { isResendConfigured, serverEnv } from "@/lib/env.server";

export type EmailMessage = {
  to: string;
  subject: string;
  html: string;
  text: string;
  /** Evita mandar dos veces el mismo email si se reintenta. */
  idempotencyKey?: string;
};

/**
 * Envía un email con Resend. Sin RESEND_API_KEY lo imprime en la consola del
 * servidor (útil en desarrollo).
 */
export async function sendEmail(message: EmailMessage): Promise<{ ok: boolean }> {
  if (!isResendConfigured) {
    console.info(`[email] (sin RESEND_API_KEY, no se envía) Para: ${message.to} · ${message.subject}\n${message.text}`);
    return { ok: true };
  }
  try {
    const resend = new Resend(serverEnv.resendApiKey);
    const { error } = await resend.emails.send(
      {
        from: serverEnv.emailFrom,
        to: message.to,
        replyTo: siteConfig.contact.email,
        subject: message.subject,
        html: message.html,
        text: message.text,
      },
      message.idempotencyKey ? { idempotencyKey: message.idempotencyKey } : undefined,
    );
    if (error) {
      console.error("[email] Resend rechazó el envío", { to: message.to, subject: message.subject, error });
      return { ok: false };
    }
    return { ok: true };
  } catch (error) {
    console.error("[email] Error enviando", error);
    return { ok: false };
  }
}
