import type { Metadata } from "next";
import Link from "next/link";
import FileUploadWorkspace from "@/components/FileUploadWorkspace";

export const metadata: Metadata = {
  title: "Analyze File — DocGuard",
};

export default function AnalyzeFilePage() {
  return (
    <>
      <div className="toolbar">
        <h1 className="toolbar__title">Analyze File</h1>
        <div className="toolbar__links">
          <Link href="/analyze" className="toolbar__link">
            Text
          </Link>
          <Link href="/analyze/file" className="toolbar__link toolbar__link--active">
            File
          </Link>
        </div>
      </div>
      <FileUploadWorkspace mode="analyze" />
    </>
  );
}
