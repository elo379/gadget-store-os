"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { getAccessToken } from "@/lib/session";

export function AuthGate({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const check = () => {
      const token = getAccessToken();

      if (pathname !== "/login" && pathname !== "/activate" && !token) {
        router.replace("/login");
        return;
      }

      setReady(true);
    };

    check();

    const timer = window.setInterval(check, 300);

    return () => window.clearInterval(timer);
  }, [pathname, router]);

  if (pathname === "/login" || pathname === "/activate") {
    return <>{children}</>;
  }

  if (!ready) {
    return null;
  }

  return <>{children}</>;
}
