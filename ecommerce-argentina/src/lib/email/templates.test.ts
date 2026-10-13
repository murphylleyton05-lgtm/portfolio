import { describe, expect, it } from "vitest";
import type { OrderWithItems } from "@/lib/orders/queries";
import { escapeHtml, newOrderNotificationEmail, orderConfirmationEmail, orderStatusEmail } from "./templates";

const order = {
  id: "11111111-1111-4111-8111-111111111111",
  number: 1042,
  access_token: "22222222-2222-4222-8222-222222222222",
  status: "paid",
  customer_name: "Ana <script>alert(1)</script> Pérez",
  customer_email: "ana@example.com",
  customer_phone: "11 2345-6789",
  customer_dni: null,
  delivery_method: "shipping",
  shipping_address: { street: "Av. Rivadavia", number: "1234", city: "CABA", province: "Ciudad Autónoma de Buenos Aires", postalCode: "C1406ABC" },
  shipping_zone: "CABA",
  subtotal: 49980,
  shipping_cost: 4500,
  total: 54480,
  notes: "Tocar timbre <b>B</b>",
  items: [
    { id: "i1", product_name: "Remera Básica", variant_name: "M", unit_price: 24990, quantity: 2, image: null, sku: "REM-M" },
  ],
} as unknown as OrderWithItems;

describe("emails de pedidos", () => {
  it("escapa HTML de datos que carga el cliente", () => {
    const { html } = orderConfirmationEmail(order, "https://tienda.com/pedido/x");
    expect(html).not.toContain("<script>");
    expect(html).toContain("&lt;b&gt;B&lt;/b&gt;");
    expect(escapeHtml(`"'<>&`)).toBe("&quot;&#39;&lt;&gt;&amp;");
  });

  it("la confirmación incluye número, items, total y link al pedido", () => {
    const { subject, html, text } = orderConfirmationEmail(order, "https://tienda.com/pedido/x?token=y");
    expect(subject).toContain("#1042");
    expect(html).toContain("Remera Básica");
    expect(html).toMatch(/\$\s?54\.480/);
    expect(html).toContain("https://tienda.com/pedido/x?token=y");
    expect(text).toContain("C1406ABC");
  });

  it("el aviso a la tienda trae los datos de contacto del cliente", () => {
    const { subject, text } = newOrderNotificationEmail(order, "https://tienda.com/admin/pedidos/x");
    expect(subject).toContain("Nueva venta");
    expect(text).toContain("ana@example.com");
    expect(text).toContain("11 2345-6789");
  });

  it("el aviso de estado distingue envío y retiro", () => {
    expect(orderStatusEmail({ ...order, status: "shipped" }, "u").subject).toContain("en camino");
    expect(orderStatusEmail({ ...order, status: "ready_for_pickup" }, "u").subject).toContain("listo para retirar");
  });
});
