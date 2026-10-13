import type { Metadata, Viewport } from "next";
import type { CSSProperties } from "react";
import { Geist, Geist_Mono } from "next/font/google";
import { siteConfig } from "@site-config";
import { publicEnv } from "@/lib/env";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  metadataBase: new URL(publicEnv.siteUrl),
  title: {
    default: `${siteConfig.name} · ${siteConfig.tagline}`,
    template: `%s · ${siteConfig.name}`,
  },
  description: siteConfig.description,
  keywords: [...siteConfig.keywords],
  applicationName: siteConfig.name,
  openGraph: {
    type: "website",
    locale: siteConfig.locale.replace("-", "_"),
    siteName: siteConfig.name,
    title: siteConfig.name,
    description: siteConfig.description,
    ...(siteConfig.ogImage ? { images: [siteConfig.ogImage] } : {}),
  },
  twitter: { card: "summary_large_image", title: siteConfig.name, description: siteConfig.description },
  formatDetection: { telephone: false },
};

export const viewport: Viewport = {
  themeColor: siteConfig.colors.primary,
  width: "device-width",
  initialScale: 1,
};

/** Los colores de site.config.ts se exponen como variables CSS --brand-*. */
const brandVars = {
  "--brand-primary": siteConfig.colors.primary,
  "--brand-primary-foreground": siteConfig.colors.primaryForeground,
  "--brand-accent": siteConfig.colors.accent,
  "--brand-accent-foreground": siteConfig.colors.accentForeground,
  "--brand-background": siteConfig.colors.background,
  "--brand-foreground": siteConfig.colors.foreground,
  "--brand-muted": siteConfig.colors.muted,
  "--brand-muted-foreground": siteConfig.colors.mutedForeground,
  "--brand-border": siteConfig.colors.border,
} as CSSProperties;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang={siteConfig.locale}
      style={brandVars}
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col font-sans">{children}</body>
    </html>
  );
}
