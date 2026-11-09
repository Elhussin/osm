"use client";
import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import Link from 'next/link';




export function NotFound({ error }: { error?: string }) {
  const t = useTranslations('NotFound');
  const paramsData = useParams();
  const locale = paramsData?.locale as string;

  const rtl = locale === 'ar';
  const dir = rtl ? 'rtl' : 'ltr';

  return (
    <div className=" flex flex-col items-center justify-center text-center p-4" dir={dir}>
      <h1 className="text-4xl font-bold mb-4">{t('title')}</h1>
      {error && <p className="text-red-500 text-4xl">{error}</p>}
      <p className="text-lg mb-6">{t('description')}</p>
      <Link href="/" className="text-blue-600 hover:underline">
        {t('goHome')}
      </Link>
    </div>
  );
}


