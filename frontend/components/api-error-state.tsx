"use client";

type ApiErrorStateProps = {
  message?: string;
  onRetry?: () => void | Promise<void>;
};

export function ApiErrorState({
  message = "Something went wrong while loading this data.",
  onRetry,
}: ApiErrorStateProps) {
  return (
    <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
      <p className="text-sm text-[var(--muted)]">{message}</p>

      {onRetry && (
        <button
          type="button"
          onClick={() => void onRetry()}
          className="mt-4 rounded-xl border border-[var(--border)] px-4 py-2 text-sm font-semibold"
        >
          Try again
        </button>
      )}
    </div>
  );
}
