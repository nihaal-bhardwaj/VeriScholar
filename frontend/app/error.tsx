'use client';

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-[50vh] flex flex-col items-center justify-center p-6 text-center">
      <h2 className="text-xl font-bold text-red-600 mb-2">Something went wrong!</h2>
      <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-4">
        {error?.message || "An unexpected error occurred."}
      </p>
      <button
        onClick={() => reset()}
        className="px-4 py-2 bg-zinc-100 hover:bg-white text-zinc-950 text-sm font-semibold rounded-lg transition"
      >
        Try again
      </button>
    </div>
  );
}
