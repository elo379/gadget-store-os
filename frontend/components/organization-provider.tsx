"use client";

import {
  createContext,
  useContext,
  useMemo,
} from "react";

type OrganizationContextValue = {
  organizationId: string | null;
  setOrganizationId: (organizationId: string | null) => void;
  hasOrganization: boolean;
};

const OrganizationContext =
  createContext<OrganizationContextValue | null>(null);

export function OrganizationProvider({
  children,
  organizationId,
  onOrganizationChange,
}: {
  children: React.ReactNode;
  organizationId: string | null;
  onOrganizationChange: (organizationId: string | null) => void;
}) {
  const value = useMemo(
    () => ({
      organizationId,
      hasOrganization: Boolean(organizationId),
      setOrganizationId: onOrganizationChange,
    }),
    [organizationId, onOrganizationChange],
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
