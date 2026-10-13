import { z } from "zod";

/**
 * Variables públicas (disponibles en el navegador). Se leen con referencias
 * literales a `process.env.NEXT_PUBLIC_*` para que Next.js las inyecte en el bundle.
 */
const emptyToUndefined = (value: unknown) =>
  typeof value === "string" && value.trim() === "" ? undefined : value;

const publicSchema = z.object({
  siteUrl: z.url(),
  supabaseUrl: z.preprocess(emptyToUndefined, z.url().optional()),
  supabasePublishableKey: z.preprocess(emptyToUndefined, z.string().min(20).optional()),
});

function resolveSiteUrl() {
  const explicit = emptyToUndefined(process.env.NEXT_PUBLIC_SITE_URL);
  if (typeof explicit === "string") return explicit.replace(/\/+$/, "");
  const vercelUrl = process.env.VERCEL_PROJECT_PRODUCTION_URL ?? process.env.VERCEL_URL;
  if (vercelUrl) return `https://${vercelUrl}`;
  return "http://localhost:3000";
}

const parsedPublic = publicSchema.safeParse({
  siteUrl: resolveSiteUrl(),
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL,
  supabasePublishableKey: process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
});

if (!parsedPublic.success) {
  throw new Error(
    `Variables de entorno públicas inválidas:\n${z.prettifyError(parsedPublic.error)}`,
  );
}

export const publicEnv = parsedPublic.data;

/** true cuando hay URL + publishable key: el catálogo se lee de Supabase. */
export const isSupabaseConfigured = Boolean(
  publicEnv.supabaseUrl && publicEnv.supabasePublishableKey,
);

export function absoluteUrl(path = "/") {
  return new URL(path, `${publicEnv.siteUrl}/`).toString();
}
