"use client";

import { useEffect, useState } from "react";
import { apiDelete, apiGet, clearToken } from "@/lib/api";
import { registerPasskey, supportsPasskeys } from "@/lib/passkeys";
import { Modal } from "@/components/premium-ui";

type Passkey = {
  id: string;
  name: string;
  last_used_at: string | null;
  created_at: string | null;
  revoked: boolean;
};

export default function SecurityPage() {
  const [passkeys, setPasskeys] = useState<Passkey[]>([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [passkeySupported, setPasskeySupported] = useState(false);
  const [showPasskeyModal, setShowPasskeyModal] = useState(false);
  const [passkeyName, setPasskeyName] = useState("This device");

  async function loadPasskeys() {
    try {
      const result = await apiGet<Passkey[]>("/auth/passkeys");
      setPasskeys(result);
    } catch {
      setMessage("Unable to load passkeys.");
    }
  }

  useEffect(() => {
    const supported = supportsPasskeys();
    queueMicrotask(() => setPasskeySupported(supported));
    if (supported) queueMicrotask(() => void loadPasskeys());
  }, []);

  async function addPasskey(name: string) {
    setMessage("");
    setLoading(true);
    try {
      await registerPasskey(name.trim());
      setMessage("Passkey registered successfully.");
      await loadPasskeys();
    } catch (err) {
      setMessage(
        err instanceof Error
          ? err.message
          : "Passkey registration failed.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function revokePasskey(id: string) {
    setMessage("");
    try {
      await apiDelete(`/auth/passkeys/${id}`);
      setMessage("Passkey revoked.");
      await loadPasskeys();
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "Unable to revoke passkey.",
      );
    }
  }

  function revokeSession() {
    clearToken();
    window.location.href = "/login";
  }

  function signOut() {
    clearToken();
    window.location.href = "/login";
  }

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-medium text-[var(--muted)]">
          Administration
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">Security</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Manage authentication methods and active access.
        </p>
      </header>

      <section className="rounded-2xl border border-[var(--border)] bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="font-semibold">Passkeys</h2>
            <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
              Use Face ID, Touch ID, or your device passcode for secure access.
            </p>
          </div>

          {passkeySupported && (
            <button
              type="button"
              onClick={() => setShowPasskeyModal(true)}
              className="rounded-xl bg-black px-5 py-3 text-sm font-semibold text-white"
            >
              Add passkey
            </button>
          )}
        </div>

        {passkeys.length > 0 && (
          <div className="mt-5 space-y-3">
            {passkeys.map((passkey) => (
              <div
                key={passkey.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--border)] p-4"
              >
                <div>
                  <p className="font-medium">{passkey.name}</p>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    Added{" "}
                    {passkey.created_at
                      ? new Date(passkey.created_at).toLocaleDateString()
                      : "recently"}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => void revokePasskey(passkey.id)}
                  className="rounded-xl border border-[var(--border)] px-4 py-2 text-sm font-semibold"
                >
                  Revoke
                </button>
              </div>
            ))}
          </div>
        )}

        {showPasskeyModal && (
          <Modal
            open={showPasskeyModal}
            onClose={() => setShowPasskeyModal(false)}
            title="Add a passkey"
          >
            <div className="space-y-5">
              <p className="text-sm leading-6 text-[var(--muted)]">
                Name this device before continuing. Your device will then ask
                for Face ID, Touch ID, or your passcode.
              </p>

              <input
                value={passkeyName}
                onChange={(event) => setPasskeyName(event.target.value)}
                className="w-full rounded-xl border border-[var(--border)] px-4 py-3 outline-none"
                placeholder="e.g. My iPhone"
                autoFocus
              />

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowPasskeyModal(false)}
                  className="flex-1 rounded-xl border border-[var(--border)] px-4 py-3 font-semibold"
                >
                  Cancel
                </button>

                <button
                  type="button"
                  disabled={loading || !passkeyName.trim()}
                  onClick={() => {
                    setShowPasskeyModal(false);
                    void addPasskey(passkeyName);
                  }}
                  className="flex-1 rounded-xl bg-black px-4 py-3 font-semibold text-white disabled:opacity-60"
                >
                  Continue
                </button>
              </div>
            </div>
          </Modal>
        )}

        {message && (
          <p className="mt-4 text-sm text-[var(--muted)]">{message}</p>
        )}
      </section>

      <section className="rounded-2xl border border-[var(--border)] bg-white p-6">
        <h2 className="font-semibold">Current session</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Your authenticated GSOS session is protected by the application
          authentication layer.
        </p>

        <div className="mt-5 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={revokeSession}
            className="rounded-xl border border-[var(--border)] px-5 py-3 text-sm font-semibold"
          >
            Revoke local session
          </button>

          <button
            type="button"
            onClick={signOut}
            className="rounded-xl bg-black px-5 py-3 text-sm font-semibold text-white"
          >
            Sign out
          </button>
        </div>
      </section>

      <section className="rounded-2xl border border-[var(--border)] bg-white p-6">
        <h2 className="font-semibold">Security principles</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {[
            ["Authentication", "Passkeys and bearer-token authentication protect account access."],
            ["Authorization", "Organization permissions determine available actions."],
            ["Auditability", "Sensitive operational actions are designed to remain traceable."],
          ].map(([title, body]) => (
            <div
              key={title}
              className="rounded-xl bg-[var(--background)] p-4"
            >
              <p className="font-medium">{title}</p>
              <p className="mt-1 text-sm text-[var(--muted)]">{body}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
