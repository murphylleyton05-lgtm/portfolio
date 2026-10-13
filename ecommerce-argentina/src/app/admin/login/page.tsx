import type { Metadata } from "next";
import Link from "next/link";
import { siteConfig } from "@site-config";
import { LoginForm } from "@/components/admin/login-form";
import { Alert } from "@/components/ui/alert";
import { isSupabaseConfigured } from "@/lib/env";

export const metadata: Metadata = { title: "Ingresar" };

export default function LoginPage() {
  return (
    <main className="flex flex-1 items-center justify-center px-4 py-16">
      <div className="flex w-full max-w-sm flex-col gap-6 rounded-2xl border border-border bg-background p-8 shadow-sm">
        <div>
          <p className="text-sm text-muted-foreground">{siteConfig.name}</p>
          <h1 className="text-2xl font-semibold tracking-tight">Panel de administración</h1>
        </div>
        {isSupabaseConfigured ? (
          <LoginForm />
        ) : (
          <Alert tone="warning" title="Falta configurar Supabase">
            Cargá las variables de Supabase en <code>.env.local</code> y creá un usuario admin (ver README).
          </Alert>
        )}
        <Link href="/" className="text-center text-sm text-muted-foreground underline-offset-4 hover:underline">
          Volver a la tienda
        </Link>
      </div>
    </main>
  );
}
