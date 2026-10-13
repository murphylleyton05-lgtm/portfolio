"use client";

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="es-AR">
      <body style={{ fontFamily: "system-ui, sans-serif", padding: "4rem 1rem", maxWidth: 640, margin: "0 auto" }}>
        <h1>Algo salió mal</h1>
        <p>Tuvimos un problema inesperado. Probá recargar la página.</p>
        <button type="button" onClick={reset} style={{ padding: "0.75rem 1.25rem", marginTop: "1rem" }}>
          Reintentar
        </button>
      </body>
    </html>
  );
}
