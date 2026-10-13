import { describe, expect, it } from "vitest";
import { siteConfig } from "@site-config";
import { deliveryMethods, findShippingZone, quoteShipping } from "./shipping";

const threshold = siteConfig.shipping.freeShippingThreshold ?? Infinity;

describe("findShippingZone", () => {
  it("ubica CABA y GBA por rango de CP (también en formato CPA)", () => {
    expect(findShippingZone("1425")?.id).toBe("caba");
    expect(findShippingZone("C1406ABC")?.id).toBe("caba");
    expect(findShippingZone("B1636")?.id).toBe("gba");
  });

  it("el resto del país usa la zona por defecto", () => {
    expect(findShippingZone("5000")?.id).toBe(siteConfig.shipping.defaultZone.id);
  });

  it("CP inválido → null", () => {
    expect(findShippingZone("abc")).toBeNull();
    expect(findShippingZone(undefined)).toBeNull();
  });
});

describe("quoteShipping", () => {
  it("cobra según la zona", () => {
    const caba = siteConfig.shipping.zones.find((z) => z.id === "caba")!;
    expect(quoteShipping({ method: "shipping", postalCode: "1425", subtotal: 1000 })).toMatchObject({
      cost: caba.cost,
      free: false,
    });
  });

  it("envío gratis desde el mínimo configurado", () => {
    expect(quoteShipping({ method: "shipping", postalCode: "5000", subtotal: threshold })).toMatchObject({
      cost: 0,
      free: true,
    });
  });

  it("retiro en el local es sin cargo", () => {
    expect(quoteShipping({ method: "pickup", subtotal: 10 })).toMatchObject({ method: "pickup", cost: 0 });
  });

  it("sin CP válido no hay cotización de envío", () => {
    expect(quoteShipping({ method: "shipping", postalCode: "", subtotal: 10 })).toBeNull();
  });

  it("lista los métodos habilitados", () => {
    expect(deliveryMethods()).toEqual(["shipping", "pickup"]);
  });
});
