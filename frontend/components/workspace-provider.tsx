"use client";

import { useEffect, useState } from "react";
import {
  getCurrentUser,
  getMyOrganizations,
  type AuthUser,
} from "@/lib/api";
import {
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

  useEffect(() => {
    let active = true;

    async function loadWorkspace() {
      try {
        const [currentUser, memberships] = await Promise.all([
          getCurrentUser(),
          getMyOrganizations(),
        ]);

        if (!active) return;

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
        if (active) {
          setUser(null);
        }
      }
    }

    loadWorkspace();

    return () => {
      active = false;
    };
  }, []);

  return (
    <OrganizationProvider>
      <div data-user-id={user?.user_id ?? ""}>{children}</div>
    </OrganizationProvider>
  );
}
