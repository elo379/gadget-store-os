"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="flex min-h-[60vh] items-center justify-center px-5 py-10">
      <div className="w-full max-w-md rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-7 text-center shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">
          Recovery
        </p>
        <h1 className="mt-2 text-2xl font-semibold">
          Something went wrong
        </h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          GSOS hit an unexpected problem. Your saved session is preserved.
        </p>
        <button
          type="button"
          onClick={reset}
          className="mt-6 rounded-xl bg-black px-5 py-3 text-sm font-semibold text-white"
        >
          Try again
        </button>
      </div>
    </main>
  );
}
