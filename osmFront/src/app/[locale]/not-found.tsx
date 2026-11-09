
"use client";
import { useTranslations } from 'next-intl';
import Link from 'next/link';
export default function NotFoundPage() {

  const t = useTranslations('NotFound');
    return (
    <div className="min-h-screen flex flex-col items-center justify-center text-center p-4">
      <h1 className="text-4xl font-bold mb-4">{t('title')}</h1>
      <p className="text-lg mb-6">{t('description')}</p>
      <Link href="/" className="text-blue-600 hover:underline">
        {t('goHome')}
      </Link>
    </div>
  );
}
