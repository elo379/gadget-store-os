"use client";

import {
  createContext,
  useContext,
  useMemo,
} from "react";
import { clearActiveOrganization, setActiveOrganizationId } from "@/lib/session";
import { useState } from "react";

type OrganizationContextValue = {
  organizationId: string | null;
  setOrganizationId: (organizationId: string | null) => void;
  hasOrganization: boolean;
};

const OrganizationContext =
  createContext<OrganizationContextValue | null>(null);

export function OrganizationProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [organizationId, setOrganizationIdState] = useState<string | null>(null);

  const value = useMemo(
    () => ({
      organizationId,
      hasOrganization: Boolean(organizationId),
      setOrganizationId: (nextOrganizationId: string | null) => {
        if (nextOrganizationId) setActiveOrganizationId(nextOrganizationId);
        else clearActiveOrganization();
        setOrganizationIdState(nextOrganizationId);
      },
    }),
    [organizationId, setOrganizationIdState],
  );

  return (
    <OrganizationContext.Provider value={value}>
      {children}
    </OrganizationContext.Provider>
  );
}

export function useOrganization() {
  const context = useContext(OrganizationContext);

  if (!context) {
    throw new Error(
      "useOrganization must be used inside OrganizationProvider",
    );
  }

  return context;
}
