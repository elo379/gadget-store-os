"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getCurrentUser,
  getMyOrganizations,
  type AuthUser,
} from "@/lib/api";
import {
  getAccessToken,
  getActiveOrganizationId,
  setActiveOrganizationId,
} from "@/lib/session";
import { OrganizationProvider } from "./organization-provider";

export function WorkspaceProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [user, setUser] = useState<AuthUser | null>(null);

  const loadWorkspace = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      return;
    }

    try {
      const [currentUser, memberships] = await Promise.all([
        getCurrentUser(),
        getMyOrganizations(),
      ]);

      setUser(currentUser);

      const existingOrganizationId = getActiveOrganizationId();

      const validExistingMembership = memberships.some(
        (membership) =>
          membership.organization_id === existingOrganizationId,
      );

      if (!validExistingMembership && memberships.length > 0) {
        setActiveOrganizationId(memberships[0].organization_id);
      }
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(loadWorkspace);

    const handleAuthChanged = () => {
      void loadWorkspace();
    };

    window.addEventListener("gsos:auth-changed", handleAuthChanged);

    return () => {
      window.removeEventListener(
        "gsos:auth-changed",
        handleAuthChanged,
      );
    };
  }, [loadWorkspace]);

  return (
    <OrganizationProvider>
      <div data-user-id={user?.user_id ?? ""}>{children}</div>
    </OrganizationProvider>
  );
}
