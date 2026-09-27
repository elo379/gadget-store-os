"use client";

import { useState } from "react";

type ConfirmActionProps = {
  label: string;
  confirmLabel?: string;
  message: string;
  onConfirm: () => void | Promise<void>;
  disabled?: boolean;
};

export function ConfirmAction({
  label,
  confirmLabel = "Confirm",
  message,
  onConfirm,
  disabled = false,
}: ConfirmActionProps) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  async function confirm() {
    setBusy(true);

    try {
      await onConfirm();
      setOpen(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button
        type="button"
        disabled={disabled || busy}
        onClick={() => setOpen(true)}
        className="rounded-xl border border-[var(--border)] px-4 py-2 text-sm font-semibold disabled:opacity-50"
      >
        {label}
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xl">
            <h2 className="text-lg font-semibold">Confirm action</h2>

            <p className="mt-2 text-sm text-[var(--muted)]">
              {message}
            </p>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                disabled={busy}
                onClick={() => setOpen(false)}
                className="rounded-xl border border-[var(--border)] px-4 py-2 text-sm font-semibold disabled:opacity-50"
              >
                Cancel
              </button>

              <button
                type="button"
                disabled={busy}
                onClick={() => void confirm()}
                className="rounded-xl bg-black px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
              >
                {busy ? "Working…" : confirmLabel}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
