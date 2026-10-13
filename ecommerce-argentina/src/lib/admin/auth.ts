import "server-only";
import { cache } from "react";
import { redirect } from "next/navigation";
import { connection } from "next/server";
import { isSupabaseConfigured } from "@/lib/env";
import { createSessionClient } from "@/lib/supabase/server";

export type AdminUser = { id: string; email: string };

/**
 * Usuario admin actual o null. Verifica el JWT (getClaims) y que esté en
 * admin_users (función is_admin). Se memoiza por request.
 */
export const getAdmin = cache(async (): Promise<AdminUser | null> => {
  if (!isSupabaseConfigured) return null;
  // El panel siempre se renderiza por request: validar el JWT usa la hora
  // actual y eso no puede quedar en un prerender.
  await connection();
  const supabase = await createSessionClient();
  const { data } = await supabase.auth.getClaims();
  const claims = data?.claims;
  if (!claims?.sub) return null;
  const { data: isAdmin, error } = await supabase.rpc("is_admin");
  if (error || !isAdmin) return null;
  return { id: claims.sub, email: typeof claims.email === "string" ? claims.email : "" };
});

/** Para páginas del panel: redirige al login si no es admin. */
export async function requireAdmin() {
  const admin = await getAdmin();
  if (!admin) redirect("/admin/login");
  const supabase = await createSessionClient();
  return { admin, supabase };
}

export class UnauthorizedError extends Error {
  constructor() {
    super("No autorizado");
  }
}

/** Para server actions del panel: tira error si no es admin. */
export async function requireAdminAction() {
  const admin = await getAdmin();
  if (!admin) throw new UnauthorizedError();
  const supabase = await createSessionClient();
  return { admin, supabase };
}
