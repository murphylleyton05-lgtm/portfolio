import Link from "next/link";
import { buttonClasses } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="container-page flex flex-1 flex-col items-start justify-center gap-4 py-24">
      <p className="text-sm font-medium text-accent">Error 404</p>
      <h1 className="text-3xl font-semibold tracking-tight">No encontramos esta página</h1>
      <p className="text-muted-foreground">Puede que el link esté mal escrito o que la página ya no exista.</p>
      <div className="flex gap-3">
        <Link href="/" className={buttonClasses("primary")}>
          Ir al inicio
        </Link>
        <Link href="/productos" className={buttonClasses("outline")}>
          Ver productos
        </Link>
      </div>
    </main>
  );
}
