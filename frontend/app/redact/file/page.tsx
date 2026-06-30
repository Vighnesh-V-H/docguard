import type { Metadata } from "next";
import Link from "next/link";
import FileUploadWorkspace from "@/components/FileUploadWorkspace";

export const metadata: Metadata = {
  title: "Redact File — DocGuard",
};

export default function RedactFilePage() {
  return (
    <>
      <div className="toolbar">
        <h1 className="toolbar__title">Redact File</h1>
        <div className="toolbar__links">
          <Link href="/redact" className="toolbar__link">
            Text
          </Link>
          <Link href="/redact/file" className="toolbar__link toolbar__link--active">
            File
          </Link>
        </div>
      </div>
      <FileUploadWorkspace mode="redact" />
    </>
  );
}
