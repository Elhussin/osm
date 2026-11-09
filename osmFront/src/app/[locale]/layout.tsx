// src/app/[locale]/layout.tsx
import { Cairo, Inter } from "next/font/google";
import "@/src/styles/app.css";
import { routing } from "@/src/app/i18n/routing";
import { notFound } from "next/navigation";
import { getTrenMessagesFiles } from "@/src/shared/utils/getTrenMessagesFiles";
import ClientProviders from "@/src/shared/hooks/ClientProviders";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "My App",
  description: "My cool Next.js app",
  icons: {
    icon: "/media/icon.png",
    shortcut: "/media/icon.png",
    apple: "/media/icon.png",
  },
};

const cairo = Cairo({
  subsets: ["arabic"],
  weight: ["400", "600", "700"],
  variable: "--font-alt",
});
const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "600", "700"],
  variable: "--font-main",
});

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  const lang = locale;

  if (!routing.locales.includes(lang as "en" | "ar")) {
    notFound();
  }
  // const { messages } = await getRequestConfig({locale});
  let messages: Record<string, any>;
  try {
    messages = await getTrenMessagesFiles(lang);
  } catch (error) {
    notFound();
  }

  const dir = lang === "ar" ? "rtl" : "ltr";

  return (
    <html lang={lang}>
      <body dir={dir} className={`${cairo.variable} ${inter.variable}`} data-theme="dark">
        <ClientProviders locale={lang} messages={messages}>
          {children}
        </ClientProviders>
      </body>
    </html>
  );
}
