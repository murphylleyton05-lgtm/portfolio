import { siteConfig } from "@site-config";

/** Ícono cuadrado con la inicial de la marca (para favicon, apple-icon y PWA). */
export function BrandIcon({ size, radius }: { size: number; radius: number }) {
  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: siteConfig.colors.primary,
        color: siteConfig.colors.primaryForeground,
        borderRadius: radius,
        fontSize: size * 0.6,
        fontWeight: 700,
      }}
    >
      {siteConfig.shortName.charAt(0).toUpperCase()}
    </div>
  );
}
