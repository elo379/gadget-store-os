"use client";

export function ErrorState({
  title = "Something went wrong",
  message = "We couldn't complete that request.",
  onRetry,
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-900">
      <h2 className="font-semibold">{title}</h2>
      <p className="mt-1 text-sm text-red-700">{message}</p>

      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 rounded-xl bg-red-700 px-4 py-2 text-sm font-semibold text-white"
        >
          Try again
        </button>
      )}
    </div>
  );
}
