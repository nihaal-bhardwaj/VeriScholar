'use client';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-zinc-50 text-zinc-900 flex flex-col items-center justify-center p-6 dark:bg-black dark:text-zinc-100">
        <div className="max-w-md w-full text-center space-y-4">
          <h2 className="text-2xl font-bold text-red-600">Application Error</h2>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            {error?.message || "An unexpected error occurred in the application."}
          </p>
          <button
            onClick={() => reset()}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-xl transition"
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
