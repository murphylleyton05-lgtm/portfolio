import { createHmac } from "node:crypto";
import { afterEach, describe, expect, it, vi } from "vitest";

const SECRET = "secreto-de-prueba-1234";

async function loadWithSecret(secret: string | undefined) {
  vi.resetModules();
  vi.stubEnv("MERCADOPAGO_WEBHOOK_SECRET", secret ?? "");
  return import("./mercadopago");
}

function sign(dataId: string, requestId: string, ts: string, secret = SECRET) {
  const manifest = `id:${dataId};request-id:${requestId};ts:${ts};`;
  return `ts=${ts},v1=${createHmac("sha256", secret).update(manifest).digest("hex")}`;
}

afterEach(() => vi.unstubAllEnvs());

describe("verifyWebhookSignature", () => {
  it("acepta una firma válida de Mercado Pago", async () => {
    const { verifyWebhookSignature } = await loadWithSecret(SECRET);
    const result = verifyWebhookSignature({ signature: sign("123456", "req-1", "1760000000"), requestId: "req-1", dataId: "123456" });
    expect(result).toEqual({ ok: true, verified: true });
  });

  it("rechaza firmas alteradas o con otra clave", async () => {
    const { verifyWebhookSignature } = await loadWithSecret(SECRET);
    expect(verifyWebhookSignature({ signature: sign("123456", "req-1", "1760000000", "otra"), requestId: "req-1", dataId: "123456" }).ok).toBe(false);
    expect(verifyWebhookSignature({ signature: sign("999", "req-1", "1760000000"), requestId: "req-1", dataId: "123456" }).ok).toBe(false);
    expect(verifyWebhookSignature({ signature: null, requestId: "req-1", dataId: "123456" }).ok).toBe(false);
  });

  it("sin clave secreta configurada no valida (el pago se verifica contra la API)", async () => {
    const { verifyWebhookSignature } = await loadWithSecret(undefined);
    expect(verifyWebhookSignature({ signature: null, requestId: null, dataId: "1" })).toEqual({ ok: true, verified: false });
  });
});
