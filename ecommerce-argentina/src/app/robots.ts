import type { MetadataRoute } from "next";
import { absoluteUrl } from "@/lib/env";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: "*", allow: "/", disallow: ["/admin", "/api/", "/checkout", "/carrito", "/pedido/"] }],
    sitemap: absoluteUrl("/sitemap.xml"),
  };
}
