"use client";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--background)] px-5">
      <section className="w-full max-w-md rounded-2xl border border-[var(--border)] bg-white p-7 text-center shadow-sm">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-red-600">
          Workspace error
        </p>

        <h1 className="mt-3 text-2xl font-semibold tracking-[-0.03em]">
          Something went wrong
        </h1>

        <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
          GSOS could not finish loading this screen. Your store data has not
          been changed by this error.
        </p>

        <button
          onClick={() => reset()}
          className="mt-6 h-11 rounded-xl bg-neutral-900 px-5 text-sm font-semibold text-white"
        >
          Try again
        </button>
      </section>
    </main>
  );
}
