"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/analyze", label: "Analyze" },
  { href: "/redact", label: "Redact" },
  { href: "/dashboard", label: "Dashboard" },
];

export default function Header() {
  const pathname = usePathname();
  const isLanding = pathname === "/";

  return (
    <header className={`header ${isLanding ? "header--landing" : ""}`}>
      <div className="header__inner">
        <Link href="/" className="header__logo">
          DocGuard
        </Link>
        <nav className="header__nav">
          {links.map((link) => {
            const active = pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`header__link ${active ? "header__link--active" : ""}`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
