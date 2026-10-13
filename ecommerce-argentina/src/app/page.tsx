import { siteConfig } from "@site-config";

export default function Home() {
  return (
    <main className="container-page flex flex-1 flex-col items-center justify-center gap-4 py-24 text-center">
      <h1 className="text-4xl font-semibold tracking-tight">{siteConfig.name}</h1>
      <p className="text-muted-foreground">{siteConfig.tagline}</p>
    </main>
  );
}
