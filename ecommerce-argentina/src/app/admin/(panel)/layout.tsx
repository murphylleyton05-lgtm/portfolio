import { Suspense } from "react";
import Link from "next/link";
import { siteConfig } from "@site-config";
import { AdminNav } from "@/components/admin/admin-nav";
import { UserMenu } from "@/components/admin/user-menu";

export default function AdminPanelLayout({ children }: LayoutProps<"/admin">) {
  return (
    <div className="flex flex-1 flex-col">
      <header className="sticky top-0 z-40 border-b border-border bg-background">
        <div className="flex h-14 items-center justify-between gap-4 px-4 md:px-6">
          <Link href="/admin" className="font-semibold">
            {siteConfig.name} <span className="font-normal text-muted-foreground">· Panel</span>
          </Link>
          <Suspense fallback={null}>
            <UserMenu />
          </Suspense>
        </div>
      </header>
      <div className="flex flex-1 flex-col md:flex-row">
        <aside className="border-b border-border bg-background px-2 py-2 md:w-56 md:border-r md:border-b-0 md:px-3 md:py-6">
          <Suspense fallback={null}>
            <AdminNav />
          </Suspense>
        </aside>
        <main className="min-w-0 flex-1 px-4 py-6 md:px-8">{children}</main>
      </div>
    </div>
  );
}
