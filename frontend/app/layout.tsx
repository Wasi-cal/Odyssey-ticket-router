import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Smart Ticket Router",
  description:
    "Classifies a support ticket into category, priority, and owning team.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
