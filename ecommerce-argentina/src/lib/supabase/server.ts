import "server-only";
import { cookies } from "next/headers";
import { createServerClient } from "@supabase/ssr";
import { publicEnv } from "@/lib/env";
import type { Database } from "./database.types";

/**
 * Cliente con la sesión del usuario (cookies). Respeta RLS: un admin logueado
 * puede escribir el catálogo y ver pedidos; un visitante no. Crear uno por request.
 */
export async function createSessionClient() {
  const cookieStore = await cookies();
  return createServerClient<Database>(publicEnv.supabaseUrl!, publicEnv.supabasePublishableKey!, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        try {
          for (const { name, value, options } of cookiesToSet) {
            cookieStore.set(name, value, options);
          }
        } catch {
          // Llamado desde un Server Component (no puede escribir cookies).
          // El proxy se encarga de refrescar la sesión.
        }
      },
    },
  });
}
