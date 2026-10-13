"use client";

import { useActionState } from "react";
import { requestWithdrawal, type WithdrawalState } from "@/lib/actions/withdrawal";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Field, Input, Textarea } from "@/components/ui/field";

export function WithdrawalForm() {
  const [state, action, pending] = useActionState<WithdrawalState, FormData>(requestWithdrawal, {});

  if (state.ok) {
    return (
      <Alert tone="success" title="Recibimos tu solicitud">
        Tu código de constancia es <strong>{state.code}</strong>. Te lo enviamos por email y te vamos a contactar para
        coordinar la devolución.
      </Alert>
    );
  }

  const aria = (name: keyof NonNullable<WithdrawalState["fieldErrors"]>) => ({
    id: name,
    name,
    "aria-invalid": state.fieldErrors?.[name] ? true : undefined,
  });

  return (
    <form action={action} className="flex flex-col gap-4" noValidate>
      {state.error && <Alert tone="error">{state.error}</Alert>}
      <div className="grid gap-4 sm:grid-cols-2">
        <Field id="orderNumber" label="Número de pedido" error={state.fieldErrors?.orderNumber}>
          <Input {...aria("orderNumber")} inputMode="numeric" placeholder="Ej: 1001" required />
        </Field>
        <Field id="email" label="Email de la compra" error={state.fieldErrors?.email}>
          <Input {...aria("email")} type="email" autoComplete="email" required />
        </Field>
      </div>
      <Field id="name" label="Nombre y apellido" error={state.fieldErrors?.name}>
        <Input {...aria("name")} autoComplete="name" required />
      </Field>
      <Field id="reason" label="Motivo (opcional)" error={state.fieldErrors?.reason}>
        <Textarea {...aria("reason")} maxLength={1000} />
      </Field>
      <Button type="submit" size="lg" loading={pending} className="self-start">
        Enviar solicitud
      </Button>
    </form>
  );
}
