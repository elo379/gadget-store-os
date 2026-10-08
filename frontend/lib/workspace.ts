import type { Organization } from "./api";

export function resolveActiveOrganizationId(
  memberships: Organization[],
  storedOrganizationId: string | null,
) {
  return memberships.some(
    (membership) => membership.organization_id === storedOrganizationId,
  )
    ? storedOrganizationId
    : memberships[0]?.organization_id ?? null;
}

export function resolveAndPersistActiveOrganizationId(
  memberships: Organization[],
  storedOrganizationId: string | null,
  persist: (organizationId: string | null) => void,
) {
  const organizationId = resolveActiveOrganizationId(
    memberships,
    storedOrganizationId,
  );
  persist(organizationId);
  return organizationId;
}

export function getOrganizationPermissionsPath(organizationId: string) {
  return `/organizations/${organizationId}/my-permissions`;
}
