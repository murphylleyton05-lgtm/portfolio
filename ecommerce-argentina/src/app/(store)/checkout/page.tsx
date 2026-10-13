import type { Metadata } from "next";
import { CheckoutForm } from "@/components/store/checkout-form";
import { canCreateOrders, isMercadoPagoConfigured } from "@/lib/env.server";

export const metadata: Metadata = { title: "Finalizar compra", robots: { index: false } };

export default function CheckoutPage() {
  return (
    <div className="container-page py-8">
      <h1 className="mb-6 text-2xl font-semibold tracking-tight sm:text-3xl">Finalizar compra</h1>
      <CheckoutForm
        ordersEnabled={canCreateOrders}
        submitLabel={isMercadoPagoConfigured ? "Pagar con Mercado Pago" : "Confirmar pedido"}
      />
    </div>
  );
}
