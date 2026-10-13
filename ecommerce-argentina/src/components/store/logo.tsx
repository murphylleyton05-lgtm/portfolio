import Image from "next/image";
import Link from "next/link";
import { siteConfig } from "@site-config";

export function Logo() {
  return (
    <Link
      href="/"
      className="flex items-center gap-2 font-semibold tracking-tight"
      aria-label={`${siteConfig.name}, ir al inicio`}
    >
      {siteConfig.logo && (
        <Image src={siteConfig.logo.src} alt="" width={siteConfig.logo.width} height={siteConfig.logo.height} preload />
      )}
      <span className="text-lg">{siteConfig.name}</span>
    </Link>
  );
}
