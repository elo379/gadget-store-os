"use client";

import { useEffect, useState } from "react";
import { getCurrentUser, type AuthUser } from "@/lib/api";
import { OrganizationProvider } from "./organization-provider";

export function WorkspaceProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    let active = true;

    async function loadUser() {
      try {
        const currentUser = await getCurrentUser();

        if (active) {
          setUser(currentUser);
        }
      } catch {
        if (active) {
          setUser(null);
        }
      }
    }

    loadUser();

    return () => {
      active = false;
    };
  }, []);

  return (
    <OrganizationProvider>
      <div data-user-id={user?.id ?? ""}>{children}</div>
    </OrganizationProvider>
  );
}
