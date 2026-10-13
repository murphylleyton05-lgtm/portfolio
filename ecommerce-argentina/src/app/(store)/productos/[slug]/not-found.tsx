import Link from "next/link";
import { buttonClasses } from "@/components/ui/button";

export default function ProductNotFound() {
  return (
    <div className="container-page flex flex-col items-start gap-4 py-24">
      <h1 className="text-2xl font-semibold">No encontramos ese producto</h1>
      <p className="text-muted-foreground">Puede que ya no esté disponible o que el link esté mal escrito.</p>
      <Link href="/productos" className={buttonClasses("primary")}>
        Ver todos los productos
      </Link>
    </div>
  );
}
