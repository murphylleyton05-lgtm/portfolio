import type { MetadataRoute } from "next";
import { siteConfig } from "@site-config";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: siteConfig.name,
    short_name: siteConfig.shortName,
    description: siteConfig.description,
    start_url: "/",
    display: "standalone",
    background_color: siteConfig.colors.background,
    theme_color: siteConfig.colors.primary,
    icons: [{ src: "/apple-icon", sizes: "180x180", type: "image/png" }],
  };
}
