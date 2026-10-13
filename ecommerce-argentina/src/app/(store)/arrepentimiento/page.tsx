import type { Metadata } from "next";
import { siteConfig } from "@site-config";
import { WithdrawalForm } from "@/components/store/withdrawal-form";

export const metadata: Metadata = {
  title: "Botón de arrepentimiento",
  description: `Revocá tu compra dentro de los ${siteConfig.legal.withdrawalDays} días corridos de recibido el producto.`,
};

export default function WithdrawalPage() {
  return (
    <div className="container-page max-w-2xl py-10">
      <h1 className="mb-3 text-2xl font-semibold tracking-tight sm:text-3xl">Botón de arrepentimiento</h1>
      <p className="mb-8 text-sm text-muted-foreground">
        Podés revocar tu compra dentro de los {siteConfig.legal.withdrawalDays} días corridos desde que recibiste el
        producto o celebraste el contrato, lo último que ocurra (Ley 24.240, art. 34 y Res. 424/2020). Completá el
        formulario y te enviamos un código de constancia por email.
      </p>
      <WithdrawalForm />
    </div>
  );
}
