import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BenchMind AI — Engineering Diagnostic Workspace",
  description: "Evidence-grounded multimodal engineering debugging with specialist agents.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
