import type { Metadata } from "next";
import Link from "next/link";
import RedactWorkspace from "@/components/RedactWorkspace";

export const metadata: Metadata = {
  title: "Redact — DocGuard",
};

export default function RedactPage() {
  return (
    <>
      <div className="toolbar">
        <h1 className="toolbar__title">Redact Text</h1>
        <div className="toolbar__links">
          <Link href="/redact" className="toolbar__link toolbar__link--active">
            Text
          </Link>
          <Link href="/redact/file" className="toolbar__link">
            File
          </Link>
        </div>
      </div>
      <RedactWorkspace />
    </>
  );
}
