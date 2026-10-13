import "server-only";
import { createClient } from "@supabase/supabase-js";
import { publicEnv } from "@/lib/env";
import { canCreateOrders, serverEnv } from "@/lib/env.server";
import type { Database } from "./database.types";

/**
 * Cliente con la SECRET KEY: saltea RLS. Solo para el servidor (checkout,
 * webhook de pagos, página de pedido con token). Nunca importarlo en el cliente.
 */
export function createServiceClient() {
  if (!canCreateOrders) {
    throw new Error("Falta configurar Supabase (URL, publishable key y SUPABASE_SECRET_KEY).");
  }
  return createClient<Database>(publicEnv.supabaseUrl!, serverEnv.supabaseSecretKey!, {
    auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
  });
}
