"use client";

type ActionFeedbackProps = {
  message: string;
  error?: boolean;
};

export function ActionFeedback({
  message,
  error = false,
}: ActionFeedbackProps) {
  if (!message) return null;

  return (
    <div
      role="status"
      className={`rounded-xl border p-3 text-sm ${
        error
          ? "border-red-200 bg-red-50 text-red-700"
          : "border-[var(--border)] bg-[var(--surface)] text-[var(--muted)]"
      }`}
    >
      {message}
    </div>
  );
}
