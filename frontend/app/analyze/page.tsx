import type { Metadata } from "next";
import Link from "next/link";
import AnalyzeWorkspace from "@/components/AnalyzeWorkspace";

export const metadata: Metadata = {
  title: "Analyze — DocGuard",
};

export default function AnalyzePage() {
  return (
    <>
      <div className="toolbar">
        <h1 className="toolbar__title">Analyze Text</h1>
        <div className="toolbar__links">
          <Link href="/analyze" className="toolbar__link toolbar__link--active">
            Text
          </Link>
          <Link href="/analyze/file" className="toolbar__link">
            File
          </Link>
        </div>
      </div>
      <AnalyzeWorkspace />
    </>
  );
}
