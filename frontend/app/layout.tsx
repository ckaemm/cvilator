import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Sidebar } from "@/components/sidebar";
import { ToastProvider } from "@/components/toast";
import { ErrorBoundary } from "@/components/error-boundary";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CVilator - ATS CV Optimizasyonu",
  description: "AI destekli CV analizi ve ATS optimizasyonu",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr" className="dark">
      <body className={inter.className}>
        <ToastProvider>
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 lg:pl-64">
              <div className="mx-auto max-w-5xl px-4 py-8 pt-16 lg:pt-8">
                <ErrorBoundary>{children}</ErrorBoundary>
              </div>
            </main>
          </div>
        </ToastProvider>
      </body>
    </html>
  );
}
