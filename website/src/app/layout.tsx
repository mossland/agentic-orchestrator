import type { Metadata } from "next";
import { JetBrains_Mono } from "next/font/google";
import { I18nProvider } from "@/lib/i18n";
import { Navigation } from "@/components/Navigation";
import { Footer } from "@/components/Footer";
import "./globals.css";

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "MOSS.AO // Agentic Orchestrator",
  description: "Multi-agent AI orchestration system for Mossland ecosystem",
  keywords: ["AI", "agents", "orchestrator", "mossland", "crypto", "debate"],
  authors: [{ name: "Mossland" }],
  openGraph: {
    title: "MOSS.AO // Agentic Orchestrator",
    description: "Multi-agent AI orchestration system for Mossland ecosystem",
    url: "https://ao.moss.land",
    siteName: "Mossland AO",
    type: "website",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Mossland Agentic Orchestrator",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "MOSS.AO // Agentic Orchestrator",
    description: "Multi-agent AI orchestration system for Mossland ecosystem",
  },
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className="dark">
      <head>
        <meta name="theme-color" content="#0a0a0a" />
        <meta name="color-scheme" content="dark" />
      </head>
      <body className={`${jetbrainsMono.variable} font-mono antialiased`}>
        <I18nProvider>
          <div className="relative min-h-screen bg-[#0a0a0a]">
            <Navigation />
            <main className="relative z-10">
              {children}
            </main>
            <Footer />
          </div>
        </I18nProvider>
      </body>
    </html>
  );
}
