import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VeriScholar — Research Integrity Screening",
  description:
    "A quiet second reader for every paper you submit. VeriScholar checks metadata, citations, and internal consistency against the public record.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500;1,600&family=DM+Sans:ital,opsz,wght@0,9..40,400..700;1,9..40,400..700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen flex flex-col relative" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}