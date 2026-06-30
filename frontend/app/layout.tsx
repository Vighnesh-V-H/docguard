import type { Metadata } from "next";
import type { ReactNode } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import "./globals.css";

export const metadata: Metadata = {
  title: "DocGuard — Document Security",
  description:
    "Detect and redact personally identifiable information in documents with a local AI engine. Nothing leaves your machine.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="page-shell">
          <Header />
          <main className="page-shell__main">{children}</main>
          <Footer />
        </div>
      </body>
    </html>
  );
}
