import { NextResponse, type NextRequest } from "next/server";
import { createServerClient } from "@supabase/ssr";
import { isSupabaseConfigured, publicEnv } from "@/lib/env";

/**
 * Para /admin: refresca la sesión de Supabase (cookies) y manda al login a
 * quien no tiene sesión. Es un chequeo "optimista": cada página y acción del
 * panel vuelve a verificar que el usuario sea admin (y RLS lo exige en la base).
 */
export async function proxy(request: NextRequest) {
  if (!isSupabaseConfigured) return NextResponse.next();

  let response = NextResponse.next({ request });
  const supabase = createServerClient(publicEnv.supabaseUrl!, publicEnv.supabasePublishableKey!, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet, headers) {
        for (const { name, value } of cookiesToSet) request.cookies.set(name, value);
        response = NextResponse.next({ request });
        for (const { name, value, options } of cookiesToSet) response.cookies.set(name, value, options);
        for (const [key, value] of Object.entries(headers ?? {})) response.headers.set(key, value);
      },
    },
  });

  const { data } = await supabase.auth.getClaims();
  const loggedIn = Boolean(data?.claims?.sub);
  const isLoginPage = request.nextUrl.pathname === "/admin/login";

  // Al login se puede entrar siempre (ej. una sesión que ya no es admin).
  if (!loggedIn && !isLoginPage) return redirectWithCookies(request, response, "/admin/login");
  return response;
}

function redirectWithCookies(request: NextRequest, from: NextResponse, pathname: string) {
  const url = request.nextUrl.clone();
  url.pathname = pathname;
  url.search = "";
  const redirect = NextResponse.redirect(url);
  for (const cookie of from.cookies.getAll()) redirect.cookies.set(cookie);
  return redirect;
}

export const config = {
  matcher: ["/admin/:path*"],
};
