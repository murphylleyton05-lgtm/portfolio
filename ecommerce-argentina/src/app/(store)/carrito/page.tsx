import type { Metadata } from "next";
import { CartView } from "@/components/store/cart-view";

export const metadata: Metadata = { title: "Carrito", robots: { index: false } };

export default function CartPage() {
  return (
    <div className="container-page py-8">
      <h1 className="mb-6 text-2xl font-semibold tracking-tight sm:text-3xl">Tu carrito</h1>
      <CartView />
    </div>
  );
}
