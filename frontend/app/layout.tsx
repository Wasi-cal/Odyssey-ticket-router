import type { Metadata } from "next";
import Nav from "../components/Nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "Smart Ticket Router",
  description: "Raise and track support tickets",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <Nav />
        {children}
      </body>
    </html>
  );
}
