const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "/api";

export type AuthUser = {
  user_id: string;
  email: string;
  role_name: string;
  personnel_id: string | null;
  is_owner: boolean;
  is_active: boolean;
};

export type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type Organization = {
  organization_id: string;
  name: string;
  slug?: string;
  role_name?: string;
  is_owner?: boolean;
};

const ACCESS_TOKEN_KEY = "gsos_access_token";
const REFRESH_TOKEN_KEY = "gsos_refresh_token";

type ApiErrorPayload = {
  detail?: unknown;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function getAccessToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

function getRefreshToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

function saveSession(accessToken: string, refreshToken?: string) {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);

  if (refreshToken) {
    window.localStorage.setItem(
      REFRESH_TOKEN_KEY,
      refreshToken,
    );
  }

  window.dispatchEvent(new Event("gsos:auth-changed"));
}

export function saveToken(token: string) {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearToken() {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  window.dispatchEvent(new Event("gsos:auth-changed"));
}

export async function refreshSession() {
  const refreshToken = getRefreshToken();

  if (!refreshToken) {
    clearToken();
    return false;
  }

  const response = await fetch(
    `${API_URL}/auth/refresh`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        refresh_token: refreshToken,
      }),
    },
  );

  if (!response.ok) {
    clearToken();
    return false;
  }

  const data = (await response.json()) as {
    access_token: string;
    refresh_token: string;
  };

  saveSession(
    data.access_token,
    data.refresh_token,
  );

  return true;
}

export async function login(
  email: string,
  password: string,
): Promise<LoginResponse> {
  const result = await request<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({
      email,
      password,
    }),
  });

  saveSession(result.access_token, result.refresh_token);
  return result;
}

export async function logout() {
  const refreshToken = getRefreshToken();

  if (refreshToken) {
    await fetch(`${API_URL}/auth/logout`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        refresh_token: refreshToken,
      }),
    }).catch(() => undefined);
  }

  clearToken();
  window.location.replace("/login");
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  retry = true,
): Promise<T> {
  const token = getAccessToken();
  const headers = new Headers(options.headers);

  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;

  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
    });
  } catch (err) {
    // Fetch errors can contain internal proxy hosts and request metadata. Keep
    // the actionable offline state while leaving diagnostic detail to redacted
    // server-side request logs.
    void err;
    throw new ApiError("Unable to reach GSOS. Check your connection and retry.", 0);
  }

  if (response.status === 401 && retry && path !== "/auth/refresh") {
    const refreshed = await refreshSession();

    if (refreshed) {
      return request<T>(path, options, false);
    }

    clearToken();
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const payload = (await response.json()) as ApiErrorPayload;
      if (typeof payload.detail === "string") {
        message = payload.detail;
      } else if (Array.isArray(payload.detail)) {
        message = payload.detail.map((item) => {
          if (typeof item === "string") return item;
          if (item && typeof item === "object" && "msg" in item) return String(item.msg);
          return JSON.stringify(item);
        }).join("; ");
      } else if (payload.detail) {
        message = JSON.stringify(payload.detail);
      }
    } catch {
      // Keep the status message.
    }

    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function getCurrentUser(): Promise<AuthUser> {
  return request<AuthUser>("/auth/me");
}

export async function getMyOrganizations(): Promise<Organization[]> {
  return request<Organization[]>("/organizations");
}

export async function apiGet<T>(
  path: string,
): Promise<T> {
  return request<T>(path);
}

export async function apiGetForOrganization<T>(
  path: string,
  organizationId: string,
): Promise<T> {
  return request<T>(
    `${path}${
      path.includes("?") ? "&" : "?"
    }organization_id=${encodeURIComponent(
      organizationId,
    )}`,
  );
}

export async function apiPost<T>(
  path: string,
  body: unknown,
): Promise<T> {
  return request<T>(
    path,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

export async function apiPatch<T>(
  path: string,
  body: unknown,
): Promise<T> {
  return request<T>(path, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}


export async function apiPut<T>(
  path: string,
  body: unknown,
): Promise<T> {
  return request<T>(path, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export async function apiPostForOrganization<T>(
  path: string,
  organizationId: string,
  body: unknown,
): Promise<T> {
  const separator = path.includes("?") ? "&" : "?";

  return apiPost<T>(
    `${path}${separator}organization_id=${encodeURIComponent(organizationId)}`,
    body,
  );
}

export async function apiPatchForOrganization<T>(
  path: string,
  organizationId: string,
  body: unknown,
): Promise<T> {
  const separator = path.includes("?") ? "&" : "?";

  return apiPatch<T>(
    `${path}${separator}organization_id=${encodeURIComponent(organizationId)}`,
    body,
  );
}

export async function apiDeleteForOrganization<T = unknown>(
  path: string,
  organizationId: string,
): Promise<T> {
  const separator = path.includes("?") ? "&" : "?";

  return apiDelete<T>(
    `${path}${separator}organization_id=${encodeURIComponent(organizationId)}`,
  );
}

export async function apiDelete<T>(
  path: string,
): Promise<T> {
  return request<T>(path, {
    method: "DELETE",
  });
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit,
): Promise<T> {
  return request<T>(path, options);
}
