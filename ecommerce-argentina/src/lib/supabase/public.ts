import "server-only";
import { createClient } from "@supabase/supabase-js";
import { isSupabaseConfigured, publicEnv } from "@/lib/env";
import type { Database } from "./database.types";

/**
 * Cliente anónimo SIN cookies: lee solo datos públicos (catálogo). Al no
 * depender del request se puede usar dentro de funciones con "use cache".
 */
export function createPublicClient() {
  if (!isSupabaseConfigured) {
    throw new Error("Supabase no está configurado (faltan NEXT_PUBLIC_SUPABASE_URL / PUBLISHABLE_KEY).");
  }
  return createClient<Database>(publicEnv.supabaseUrl!, publicEnv.supabasePublishableKey!, {
    auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
  });
}
