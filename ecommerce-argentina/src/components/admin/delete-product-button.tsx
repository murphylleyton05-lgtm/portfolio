import { Trash2 } from "lucide-react";
import { deleteProduct } from "@/lib/actions/admin/products";
import { Button } from "@/components/ui/button";
import { ConfirmForm } from "./confirm-form";

export function DeleteProductButton({ id, name }: { id: string; name: string }) {
  return (
    <ConfirmForm
      action={deleteProduct}
      message={`¿Borrar "${name}"? No se puede deshacer. (Si solo querés ocultarlo, usá "Pausar".)`}
    >
      <input type="hidden" name="id" value={id} />
      <Button type="submit" variant="danger" size="sm">
        <Trash2 className="size-4" aria-hidden /> Borrar
      </Button>
    </ConfirmForm>
  );
}
