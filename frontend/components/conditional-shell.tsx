"use client";

import { usePathname } from "next/navigation";
import { AppShell } from "@/components/app-shell";

export function ConditionalShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  if (["/login", "/activate", "/create-organization", "/privacy", "/guide"].includes(pathname)) {
    return <>{children}</>;
  }

  return <AppShell>{children}</AppShell>;
}
