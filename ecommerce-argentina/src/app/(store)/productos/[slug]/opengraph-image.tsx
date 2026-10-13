import { ImageResponse } from "next/og";
import { siteConfig } from "@site-config";
import { getProductBySlug } from "@/lib/catalog/data";
import { formatPrice } from "@/lib/utils";

export const alt = "Producto";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

/** Imagen para compartir en redes: nombre, precio y marca con los colores de la config. */
export default async function OpenGraphImage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const product = await getProductBySlug(slug);
  const { colors } = siteConfig;

  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        padding: 72,
        background: colors.muted,
        color: colors.foreground,
      }}
    >
      <div style={{ display: "flex", fontSize: 32, fontWeight: 700 }}>{siteConfig.name}</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        <div style={{ display: "flex", fontSize: 72, fontWeight: 700, lineHeight: 1.1 }}>
          {product?.name ?? siteConfig.name}
        </div>
        {product && (
          <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
            <div
              style={{
                display: "flex",
                fontSize: 44,
                fontWeight: 700,
                background: colors.primary,
                color: colors.primaryForeground,
                padding: "12px 28px",
                borderRadius: 16,
              }}
            >
              {product.hasPriceRange ? `Desde ${formatPrice(product.minPrice)}` : formatPrice(product.minPrice)}
            </div>
            {product.category && (
              <div style={{ display: "flex", fontSize: 32, color: colors.mutedForeground }}>
                {product.category.name}
              </div>
            )}
          </div>
        )}
      </div>
      <div style={{ display: "flex", fontSize: 28, color: colors.mutedForeground }}>{siteConfig.tagline}</div>
    </div>,
    size,
  );
}
