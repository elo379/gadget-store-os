"use client";

import {
  createContext,
  useContext,
  useMemo,
} from "react";
import { getActiveOrganizationId, setActiveOrganizationId } from "@/lib/session";
import { usePersistedState } from "@/hooks/use-persisted-state";

type OrganizationContextValue = {
  organizationId: string | null;
  setOrganizationId: (organizationId: string) => void;
  hasOrganization: boolean;
};

const OrganizationContext =
  createContext<OrganizationContextValue | null>(null);

export function OrganizationProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [organizationId, setOrganizationIdState] =
    usePersistedState<string | null>(
      "gsos_active_organization",
      getActiveOrganizationId(),
    );

  const value = useMemo(
    () => ({
      organizationId,
      hasOrganization: Boolean(organizationId),
      setOrganizationId: (nextOrganizationId: string) => {
        setActiveOrganizationId(nextOrganizationId);
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
