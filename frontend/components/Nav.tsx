"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearSession, getToken, getUserEmail } from "../lib/auth";

const LINKS = [
  { href: "/", label: "Raise a ticket" },
  { href: "/tickets", label: "My tickets" },
  { href:"/aimanual", label: "AI vs. Manual"}
];

export default function Nav() {
  const pathname = usePathname();
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    setEmail(getToken() ? getUserEmail() : null);
  }, [pathname]);

  function handleLogout() {
    clearSession();
    setEmail(null);
    router.push("/login");
  }

  return (
    <nav className="topnav">
      <Link href="/" className="brand">
        Smart Ticket Router
      </Link>
      {LINKS.map(({ href, label }) => {
        const active =
          href === "/" ? pathname === "/" : pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            className={`navlink${active ? " active" : ""}`}
          >
            {label}
          </Link>
        );
      })}
      <span style={{ marginLeft: "auto" }} />
      {email ? (
        <>
          <span className="navlink" style={{ cursor: "default" }}>
            {email}
          </span>
          <a
            href="#"
            className="navlink"
            onClick={(e) => {
              e.preventDefault();
              handleLogout();
            }}
          >
            Log out
          </a>
        </>
      ) : (
        <Link
          href="/login"
          className={`navlink${pathname === "/login" ? " active" : ""}`}
        >
          Log in
        </Link>
      )}
    </nav>
  );
}
