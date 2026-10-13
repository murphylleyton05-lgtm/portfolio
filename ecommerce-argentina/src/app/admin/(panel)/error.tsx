"use client";

import { useEffect } from "react";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

export default function AdminError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => console.error(error), [error]);
  return (
    <div className="flex flex-col items-start gap-4">
      <Alert tone="error" title="No pudimos cargar esta sección">
        {error.message || "Error inesperado."} {error.digest ? `(código ${error.digest})` : ""}
      </Alert>
      <Button onClick={reset}>Reintentar</Button>
    </div>
  );
}
