import type { NextConfig } from "next";

// En Vercel, si no se definió NEXT_PUBLIC_SITE_URL usamos el dominio de producción
// del proyecto, así links de emails, back_urls de Mercado Pago y SEO apuntan bien.
const siteUrl =
  process.env.NEXT_PUBLIC_SITE_URL ||
  (process.env.VERCEL_PROJECT_PRODUCTION_URL
    ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
    : "http://localhost:3000");

function supabaseImagesPattern() {
  const raw = process.env.NEXT_PUBLIC_SUPABASE_URL;
  try {
    if (raw) {
      const url = new URL(raw);
      return {
        protocol: url.protocol.replace(":", "") as "http" | "https",
        hostname: url.hostname,
        port: url.port,
        pathname: "/storage/v1/object/public/**",
      };
    }
  } catch {
    // URL inválida: la validación de env.ts lo reporta con un mensaje claro.
  }
  return { protocol: "https" as const, hostname: "*.supabase.co", pathname: "/storage/v1/object/public/**" };
}

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "X-Frame-Options", value: "SAMEORIGIN" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
];

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  env: {
    NEXT_PUBLIC_SITE_URL: siteUrl.replace(/\/+$/, ""),
  },
  images: {
    remotePatterns: [supabaseImagesPattern()],
    qualities: [75, 90],
  },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
