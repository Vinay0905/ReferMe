import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ALLEN NEET Test ↔ Topic Intelligence Studio",
  description: "Fast bidirectional NEET test and topic discovery with instant syllabus and question paper preview",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0A0518] text-[#EEEEEE] antialiased">
        <div className="ambient-glow" />
        <div className="relative z-10">{children}</div>
      </body>
    </html>
  );
}
