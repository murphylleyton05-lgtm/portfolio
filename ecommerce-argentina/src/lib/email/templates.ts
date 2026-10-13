import { siteConfig } from "@site-config";
import { formatAddress, shippingAddressOf, type OrderWithItems } from "@/lib/orders/queries";
import { formatPrice, whatsappUrl } from "@/lib/utils";

/** Escapa texto para insertarlo en HTML (todos los datos del cliente pasan por acá). */
export function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

const { colors } = siteConfig;
const font = "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;";

function layout({ preheader, body }: { preheader: string; body: string }) {
  return `<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHtml(siteConfig.name)}</title></head>
<body style="margin:0;padding:0;background:${colors.muted};${font}color:${colors.foreground};">
<span style="display:none;max-height:0;overflow:hidden;opacity:0">${escapeHtml(preheader)}</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:${colors.muted};padding:24px 12px;">
<tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:${colors.background};border-radius:12px;overflow:hidden;">
<tr><td style="background:${colors.primary};color:${colors.primaryForeground};padding:20px 24px;font-size:18px;font-weight:700;">${escapeHtml(siteConfig.name)}</td></tr>
<tr><td style="padding:24px;font-size:15px;line-height:1.5;">${body}</td></tr>
<tr><td style="padding:16px 24px;border-top:1px solid ${colors.border};font-size:12px;color:${colors.mutedForeground};">
${escapeHtml(siteConfig.name)} · ${escapeHtml(siteConfig.contact.address)}<br>
¿Dudas? Respondé este email o escribinos por <a href="${whatsappUrl(siteConfig.contact.whatsappDefaultMessage)}" style="color:${colors.mutedForeground};">WhatsApp</a>.
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>`;
}

function button(href: string, label: string) {
  return `<a href="${escapeHtml(href)}" style="display:inline-block;background:${colors.primary};color:${colors.primaryForeground};text-decoration:none;padding:12px 20px;border-radius:8px;font-weight:600;">${escapeHtml(label)}</a>`;
}

function itemsTable(order: OrderWithItems) {
  const rows = order.items
    .map((item) => {
      const variant =
        item.variant_name !== "Único"
          ? ` <span style="color:${colors.mutedForeground}">(${escapeHtml(item.variant_name)})</span>`
          : "";
      return `<tr>
<td style="padding:8px 0;border-bottom:1px solid ${colors.border};">${item.quantity} × ${escapeHtml(item.product_name)}${variant}</td>
<td style="padding:8px 0;border-bottom:1px solid ${colors.border};text-align:right;white-space:nowrap;">${formatPrice(Number(item.unit_price) * item.quantity)}</td>
</tr>`;
    })
    .join("");
  const shippingLabel =
    order.delivery_method === "pickup"
      ? "Retiro en el local"
      : `Envío${order.shipping_zone ? ` (${escapeHtml(order.shipping_zone)})` : ""}`;
  return `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;margin:16px 0;">
${rows}
<tr><td style="padding:8px 0;">Subtotal</td><td style="padding:8px 0;text-align:right;">${formatPrice(Number(order.subtotal))}</td></tr>
<tr><td style="padding:4px 0;">${shippingLabel}</td><td style="padding:4px 0;text-align:right;">${Number(order.shipping_cost) ? formatPrice(Number(order.shipping_cost)) : "Gratis"}</td></tr>
<tr><td style="padding:8px 0;font-weight:700;font-size:16px;">Total</td><td style="padding:8px 0;text-align:right;font-weight:700;font-size:16px;">${formatPrice(Number(order.total))}</td></tr>
</table>`;
}

function deliveryText(order: OrderWithItems) {
  if (order.delivery_method === "pickup") {
    return `Retiro en ${siteConfig.pickup.address} (${siteConfig.pickup.hours}). ${siteConfig.pickup.instructions}`;
  }
  const address = shippingAddressOf(order);
  return `Envío a ${address ? formatAddress(address) : "la dirección indicada"}.`;
}

function itemsText(order: OrderWithItems) {
  return order.items
    .map(
      (item) =>
        `- ${item.quantity} x ${item.product_name}${item.variant_name !== "Único" ? ` (${item.variant_name})` : ""}: ${formatPrice(Number(item.unit_price) * item.quantity)}`,
    )
    .join("\n");
}

/** Confirmación al cliente cuando se aprueba el pago. */
export function orderConfirmationEmail(order: OrderWithItems, orderUrl: string) {
  const firstName = order.customer_name.split(" ")[0];
  const subject = `¡Gracias por tu compra! Pedido #${order.number} confirmado`;
  const html = layout({
    preheader: `Recibimos el pago de tu pedido #${order.number}.`,
    body: `
<h1 style="margin:0 0 8px;font-size:22px;">¡Gracias, ${escapeHtml(firstName)}!</h1>
<p style="margin:0 0 16px;">Recibimos el pago de tu pedido <strong>#${order.number}</strong> y ya lo estamos preparando.</p>
${itemsTable(order)}
<p style="margin:0 0 8px;"><strong>Entrega:</strong> ${escapeHtml(deliveryText(order))}</p>
${order.notes ? `<p style="margin:0 0 8px;"><strong>Tus notas:</strong> ${escapeHtml(order.notes)}</p>` : ""}
<p style="margin:24px 0;">${button(orderUrl, "Ver mi pedido")}</p>
<p style="margin:0;color:${colors.mutedForeground};font-size:13px;">Te vamos a avisar por email cuando ${order.delivery_method === "pickup" ? "esté listo para retirar" : "lo despachemos"}.</p>`,
  });
  const text = `¡Gracias, ${firstName}!

Recibimos el pago de tu pedido #${order.number}.

${itemsText(order)}
Envío: ${Number(order.shipping_cost) ? formatPrice(Number(order.shipping_cost)) : "Gratis"}
Total: ${formatPrice(Number(order.total))}

Entrega: ${deliveryText(order)}

Ver tu pedido: ${orderUrl}

${siteConfig.name}`;
  return { subject, html, text };
}

/** Aviso a la tienda de una venta nueva. */
export function newOrderNotificationEmail(order: OrderWithItems, adminUrl: string) {
  const subject = `Nueva venta: pedido #${order.number} · ${formatPrice(Number(order.total))}`;
  const html = layout({
    preheader: `${order.customer_name} pagó ${formatPrice(Number(order.total))}.`,
    body: `
<h1 style="margin:0 0 8px;font-size:20px;">Nueva venta 🎉</h1>
<p style="margin:0 0 8px;"><strong>${escapeHtml(order.customer_name)}</strong> · ${escapeHtml(order.customer_email)} · ${escapeHtml(order.customer_phone)}</p>
${itemsTable(order)}
<p style="margin:0 0 8px;"><strong>Entrega:</strong> ${escapeHtml(deliveryText(order))}</p>
${order.notes ? `<p style="margin:0 0 8px;"><strong>Notas:</strong> ${escapeHtml(order.notes)}</p>` : ""}
<p style="margin:24px 0 0;">${button(adminUrl, "Ver en el panel")}</p>`,
  });
  const text = `Nueva venta: pedido #${order.number}
Cliente: ${order.customer_name} · ${order.customer_email} · ${order.customer_phone}

${itemsText(order)}
Total: ${formatPrice(Number(order.total))}

Entrega: ${deliveryText(order)}
${order.notes ? `Notas: ${order.notes}\n` : ""}
Panel: ${adminUrl}`;
  return { subject, html, text };
}

/** Aviso al cliente cuando el pedido se despacha o está listo para retirar. */
export function orderStatusEmail(order: OrderWithItems, orderUrl: string) {
  const ready = order.status === "ready_for_pickup";
  const subject = ready
    ? `Tu pedido #${order.number} está listo para retirar`
    : `Tu pedido #${order.number} está en camino`;
  const message = ready
    ? `Ya podés retirar tu pedido en ${siteConfig.pickup.address} (${siteConfig.pickup.hours}). Traé tu DNI o el número de pedido.`
    : `Despachamos tu pedido. ${deliveryText(order)}`;
  const html = layout({
    preheader: subject,
    body: `
<h1 style="margin:0 0 8px;font-size:22px;">${escapeHtml(subject)}</h1>
<p style="margin:0 0 16px;">${escapeHtml(message)}</p>
<p style="margin:24px 0 0;">${button(orderUrl, "Ver mi pedido")}</p>`,
  });
  return { subject, html, text: `${subject}\n\n${message}\n\nVer tu pedido: ${orderUrl}\n\n${siteConfig.name}` };
}
