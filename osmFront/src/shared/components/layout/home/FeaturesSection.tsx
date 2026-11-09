// app/components/FeaturesSection.tsx
"use client";

import { useTranslations } from "next-intl";
import Image from "next/image";
import { motion } from "framer-motion";

// Reusable feature item component
function FeatureItem({ text }: { text: string }) {
  return (
    <li className="flex items-start space-x-2 before:content-['✓'] before:text-primary before:mr-2">
      <span>{text}</span>
    </li>
  );
}

export default function FeaturesSection() {
  const t = useTranslations("featuresSection");
  const features = t.raw("list") as Record<string, string>;

  return (
    <section
      aria-label={t("title")}
      className="relative overflow-hidden rounded-2xl bg-white/10 backdrop-blur-lg border border-white/20 p-6 lg:p-8 shadow-lg "
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.2 }}
        transition={{ duration: 0.6 }}
        className="flex flex-col lg:flex-row items-center justify-between gap-8"
      >
        {/* Textual content */}
        <div className="max-w-lg text-start space-y-6">
          <h2 className="text-3xl font-semibold text-gray-900 dark:text-gray-100">
            {t("title")}
          </h2>
          <ul className="space-y-3 text-lg text-gray-700 dark:text-gray-300">
            {Object.entries(features).map(([key, feature]) => (
              <FeatureItem key={key} text={feature} />
            ))}
          </ul>
        </div>

        {/* Image */}
        <div className="relative w-full max-w-md aspect-video overflow-hidden rounded-xl shadow-lg hover:scale-105 transition-transform duration-300">
          <Image
            src="/media/FeaturesSection.png"
            alt={t("title")}
            fill
            className="object-cover"
            priority
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"



            
          />
        </div>
      </motion.div>
    </section>
  );
}
