"use client";

import { createBrowserClient } from "@supabase/ssr";
import { publicEnv } from "@/lib/env";
import type { Database } from "./database.types";

/** Cliente del navegador (usa la sesión del admin para subir imágenes a Storage). */
export function createBrowserSupabase() {
  return createBrowserClient<Database>(publicEnv.supabaseUrl!, publicEnv.supabasePublishableKey!);
}
