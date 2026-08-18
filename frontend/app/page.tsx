export default function Home() {
  const navItems = [
    { label: "Paper Analyser", href: "/analyser" },
    { label: "Review Detector", href: "#" },
    { label: "Methodology", href: "#" },
  ];

  return (
    <div className="flex min-h-screen flex-col bg-zinc-50 font-sans dark:bg-black">
      <header className="flex w-full max-w-4xl items-center justify-between self-center px-6 py-6">
        <span className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
          Mini Project
        </span>
        <nav className="flex gap-6 text-sm text-zinc-600 dark:text-zinc-400">
          {navItems.map((item) => (
            <a key={item.label} href={item.href} className="hover:text-zinc-900 dark:hover:text-zinc-100">
              {item.label}
            </a>
          ))}
        </nav>
      </header>

      <main className="flex flex-1 flex-col items-center justify-center gap-6 px-6 text-center">
        <h1 className="max-w-2xl text-4xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          Mini Project
        </h1>
        <p className="max-w-xl text-lg leading-8 text-zinc-600 dark:text-zinc-400">
          A research-integrity screening tool. Mini Project analyses uploaded
          research papers for suspicious signals and produces explainable,
          evidence-backed risk reports.
        </p>
        <p className="max-w-xl text-sm text-zinc-500 dark:text-zinc-500">
          The Review Detector and Methodology sections are under construction.
        </p>
      </main>

      <footer className="self-center px-6 py-6 text-xs text-zinc-400">
        Screening signals only, not proof of misconduct.
      </footer>
    </div>
  );
}
