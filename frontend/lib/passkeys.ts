"use client";

import { apiPost } from "@/lib/api";

function b64(value: ArrayBuffer): string {
  return btoa(String.fromCharCode(...new Uint8Array(value)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

function buffer(value: string): ArrayBuffer {
  const padded = value.replace(/-/g, "+").replace(/_/g, "/");
  const binary = atob(padded + "=".repeat((4 - padded.length % 4) % 4));
  return Uint8Array.from(binary, (c) => c.charCodeAt(0)).buffer;
}

export function supportsPasskeys() {
  return (
    typeof window !== "undefined" &&
    typeof window.PublicKeyCredential !== "undefined"
  );
}

export async function registerPasskey(name = "This device") {
  const options = await apiPost<any>(
    "/auth/passkeys/register/options",
    { name },
  );

  const credential = await navigator.credentials.create({
    publicKey: {
      ...options,
      challenge: buffer(options.challenge),
      user: {
        ...options.user,
        id: buffer(options.user.id),
      },
      excludeCredentials: (options.excludeCredentials || []).map(
        (item: any) => ({
          ...item,
          id: buffer(item.id),
        }),
      ),
    },
  });

  if (!(credential instanceof PublicKeyCredential)) {
    throw new Error("Passkey creation was cancelled.");
  }

  const response = credential.response as AuthenticatorAttestationResponse;

  return apiPost("/auth/passkeys/register/verify", {
    name,
    credential_id: credential.id,
    raw_id: b64(credential.rawId),
    client_data_json: b64(response.clientDataJSON),
    attestation_object: b64(response.attestationObject),
  });
}

export async function authenticateWithPasskey() {
  const options = await apiPost<any>(
    "/auth/passkeys/login/options",
    {},
  );

  const credential = await navigator.credentials.get({
    publicKey: {
      ...options,
      challenge: buffer(options.challenge),
      allowCredentials: (options.allowCredentials || []).map(
        (item: any) => ({
          ...item,
          id: buffer(item.id),
        }),
      ),
    },
  });

  if (!(credential instanceof PublicKeyCredential)) {
    throw new Error("Passkey authentication was cancelled.");
  }

  const response = credential.response as AuthenticatorAssertionResponse;

  return apiPost<{ access_token: string; refresh_token: string }>("/auth/passkeys/login/verify", {
    credential_id: credential.id,
    raw_id: b64(credential.rawId),
    client_data_json: b64(response.clientDataJSON),
    authenticator_data: b64(response.authenticatorData),
    signature: b64(response.signature),
    user_handle: response.userHandle ? b64(response.userHandle) : null,
  });
}
