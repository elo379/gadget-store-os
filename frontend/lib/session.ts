const TOKEN_KEY = "gsos_access_token";
const ORGANIZATION_KEY = "gsos_active_organization";

export function getAccessToken() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(TOKEN_KEY);
}

export function saveAccessToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearSession() {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(ORGANIZATION_KEY);
}

export function getActiveOrganizationId() {
  if (typeof window === "undefined") {
    return null;
  }

  const stored = window.localStorage.getItem(ORGANIZATION_KEY);
  return stored || "10c8d676bbfc4ea0ab4cdb0cb3794754";
}

export function setActiveOrganizationId(organizationId: string) {
  window.localStorage.setItem(ORGANIZATION_KEY, organizationId);
}

export function clearActiveOrganization() {
  window.localStorage.removeItem(ORGANIZATION_KEY);
}
