import { LogOut } from "lucide-react";
import { signOut } from "@/lib/actions/auth";
import { getAdmin } from "@/lib/admin/auth";

export async function UserMenu() {
  const admin = await getAdmin();
  if (!admin) return null;
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="hidden max-w-48 truncate text-muted-foreground sm:inline">{admin.email}</span>
      <form action={signOut}>
        <button type="submit" className="inline-flex items-center gap-1 rounded-lg px-2 py-1.5 hover:bg-muted">
          <LogOut className="size-4" aria-hidden /> Salir
        </button>
      </form>
    </div>
  );
}
