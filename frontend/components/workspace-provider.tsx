"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  getCurrentUser,
  getMyOrganizations,
  type AuthUser,
} from "@/lib/api";
import {
  getAccessToken,
  getActiveOrganizationId,
  clearActiveOrganization,
  setActiveOrganizationId,
} from "@/lib/session";
import { OrganizationProvider } from "./organization-provider";
import { resolveAndPersistActiveOrganizationId } from "@/lib/workspace";

export function WorkspaceProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [organizationId, setOrganizationIdState] = useState<string | null>(null);
  const requestId = useRef(0);

  const updateOrganizationId = useCallback((nextOrganizationId: string | null) => {
    if (nextOrganizationId) setActiveOrganizationId(nextOrganizationId);
    else clearActiveOrganization();
    setOrganizationIdState(nextOrganizationId);
  }, []);

  const loadWorkspace = useCallback(async () => {
    const currentRequestId = ++requestId.current;
    if (!getAccessToken()) {
      setUser(null);
      updateOrganizationId(null);
      return;
    }

    try {
      const [currentUser, memberships] = await Promise.all([
        getCurrentUser(),
        getMyOrganizations(),
      ]);

      if (currentRequestId !== requestId.current) return;

      setUser(currentUser);

      const existingOrganizationId = getActiveOrganizationId();

      resolveAndPersistActiveOrganizationId(
        memberships,
        existingOrganizationId,
        updateOrganizationId,
      );
    } catch {
      if (currentRequestId !== requestId.current) return;
      setUser(null);
      updateOrganizationId(null);
    }
  }, [updateOrganizationId]);

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
    <OrganizationProvider
      organizationId={organizationId}
      onOrganizationChange={updateOrganizationId}
    >
      <div data-user-id={user?.user_id ?? ""}>{children}</div>
    </OrganizationProvider>
  );
}
