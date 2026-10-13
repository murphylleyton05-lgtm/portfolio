"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Button, buttonClasses } from "@/components/ui/button";

export default function StoreError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="container-page flex flex-col items-start gap-4 py-24">
      <h1 className="text-2xl font-semibold">Algo salió mal</h1>
      <p className="text-muted-foreground">
        Tuvimos un problema al cargar esta página. Probá de nuevo en unos segundos.
      </p>
      {error.digest && <p className="text-xs text-muted-foreground">Código: {error.digest}</p>}
      <div className="flex gap-3">
        <Button onClick={reset}>Reintentar</Button>
        <Link href="/" className={buttonClasses("outline")}>
          Ir al inicio
        </Link>
      </div>
    </div>
  );
}
