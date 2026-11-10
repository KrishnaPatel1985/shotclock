import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Shotclock · ADU permit checker for California",
  description:
    "Shotclock checks ADU permit applications and city correction letters against California law, so the 60-day fast path becomes the normal path.",
  openGraph: {
    title: "Shotclock · The law says 60 days. Shotclock makes sure it happens.",
    description:
      "Pre-check your ADU application, check the city's correction letter against state law, and track the 60-day shot clock.",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@500;700&display=swap"
        />
        <link
          rel="icon"
          href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 46 46'%3E%3Crect width='46' height='46' rx='12' fill='%23E8643A'/%3E%3Crect x='19' y='7' width='8' height='4' rx='1.5' fill='%23fff'/%3E%3Ccircle cx='23' cy='25' r='12' fill='none' stroke='%23fff' stroke-width='3.2'/%3E%3Cpath d='M23 25 L23 17.5 M23 25 L28.5 28.5' stroke='%23fff' stroke-width='3.2' stroke-linecap='round'/%3E%3C/svg%3E"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
