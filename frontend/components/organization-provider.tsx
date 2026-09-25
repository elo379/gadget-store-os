"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  getActiveOrganizationId,
  setActiveOrganizationId,
} from "@/lib/session";

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
    useState<string | null>(null);

  useEffect(() => {
    setOrganizationIdState(getActiveOrganizationId());
  }, []);

  const value = useMemo(
    () => ({
      organizationId,
      hasOrganization: Boolean(organizationId),
      setOrganizationId: (nextOrganizationId: string) => {
        setActiveOrganizationId(nextOrganizationId);
        setOrganizationIdState(nextOrganizationId);
      },
    }),
    [organizationId],
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
