//  app/home/components/HeroSection.tsx
"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { useLocale } from "next-intl";
export default function HeroSection() {
  const t = useTranslations("heroSection");
  const locale = useLocale();

  return (
    <section className="py-20 px-6 text-center max-w-4xl mx-auto">
      <h1 className="text-4xl sm:text-5xl font-bold mb-6">{t("title")}</h1>
      <p className="text-lg sm:text-xl text-gray-600 dark:text-gray-300 mb-8">{t("description")}</p>
      <Link
        href={`/${locale}/auth/register`}
        className="inline-block bg-primary text-white px-6 py-3 rounded-md hover:bg-primary-dark transition"
      >
        {t("cta")}
      </Link>
    </section>
  );
}
