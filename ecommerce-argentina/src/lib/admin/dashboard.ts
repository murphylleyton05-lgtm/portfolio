import "server-only";
import { connection } from "next/server";
import type { SupabaseClient } from "@supabase/supabase-js";
import { siteConfig } from "@site-config";
import type { Database } from "@/lib/supabase/database.types";

const PAID_STATUSES = ["paid", "preparing", "shipped", "ready_for_pickup", "delivered"] as const;
const DAY = 24 * 60 * 60 * 1000;

/** Datos del inicio del panel (requiere un cliente con sesión de admin). */
export async function getDashboardData(supabase: SupabaseClient<Database>) {
  await connection();
  const since = new Date(Date.now() - 30 * DAY).toISOString();

  const [pending, toPrepare, sales, recent, lowStock] = await Promise.all([
    supabase.from("orders").select("id", { count: "exact", head: true }).eq("status", "pending_payment"),
    supabase.from("orders").select("id", { count: "exact", head: true }).in("status", ["paid", "preparing"]),
    supabase
      .from("orders")
      .select("total")
      .in("status", [...PAID_STATUSES])
      .gte("paid_at", since),
    supabase
      .from("orders")
      .select("id, number, status, customer_name, total, created_at")
      .order("created_at", { ascending: false })
      .limit(8),
    supabase
      .from("product_variants")
      .select("id, name, stock, product:products(id, name)")
      .lte("stock", siteConfig.catalog.lowStockThreshold)
      .order("stock")
      .limit(10),
  ]);

  return {
    pendingCount: pending.count ?? 0,
    toPrepareCount: toPrepare.count ?? 0,
    salesTotal: (sales.data ?? []).reduce((sum, order) => sum + Number(order.total), 0),
    salesCount: sales.data?.length ?? 0,
    recentOrders: recent.data ?? [],
    lowStock: lowStock.data ?? [],
  };
}
