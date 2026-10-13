import { ImageResponse } from "next/og";
import { siteConfig } from "@site-config";

export const alt = siteConfig.name;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

/** Imagen por defecto para compartir la tienda (usa colores y textos de site.config.ts). */
export default function OpenGraphImage() {
  const { colors } = siteConfig;
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          gap: 24,
          padding: 80,
          background: colors.primary,
          color: colors.primaryForeground,
        }}
      >
        <div style={{ display: "flex", fontSize: 88, fontWeight: 700 }}>{siteConfig.name}</div>
        <div style={{ display: "flex", fontSize: 40, opacity: 0.85 }}>{siteConfig.tagline}</div>
        <div style={{ display: "flex", width: 120, height: 10, background: colors.accent, borderRadius: 5 }} />
      </div>
    ),
    size,
  );
}
