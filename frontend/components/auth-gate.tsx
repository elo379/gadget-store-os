"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { clearSession, getAccessToken } from "@/lib/session";
import { getCurrentUser } from "@/lib/api";

export function AuthGate({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    let active = true;

    async function checkSession() {
      if (!getAccessToken()) {
        router.replace("/login");
        return;
      }

      try {
        await getCurrentUser();

        if (active) {
          setChecking(false);
        }
      } catch {
        clearSession();
        router.replace("/login");
      }
    }

    checkSession();

    return () => {
      active = false;
    };
  }, [router]);

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--background)]">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-pulse rounded-full bg-neutral-900" />
          <p className="mt-4 text-sm text-[var(--muted)]">
            Securing your workspace...
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
