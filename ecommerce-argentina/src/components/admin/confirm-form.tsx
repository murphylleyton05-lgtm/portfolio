"use client";

import type { ComponentProps } from "react";

/** <form> que pide confirmación antes de enviar (para borrados). */
export function ConfirmForm({ message, ...props }: ComponentProps<"form"> & { message: string }) {
  return (
    <form
      {...props}
      onSubmit={(event) => {
        if (!confirm(message)) event.preventDefault();
      }}
    />
  );
}
