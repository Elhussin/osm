"use client";
import { Link} from '@/src/app/i18n/navigation';
import { AlertTriangle } from "lucide-react";
import { useTranslations } from "next-intl";
export default function PayPalCancelPage() {
  const t = useTranslations('paymentCancel');
  return (
    <div className="min-h-screen flex flex-col justify-center items-center bg-yellow-50 p-6">
      <AlertTriangle className="text-yellow-600 w-20 h-20 mb-4" />
      <h1 className="text-3xl font-bold text-yellow-700">{t('title')}</h1>
      <p className="text-gray-700 mt-2 text-center max-w-md">
        {t('description')}
      </p>
      <Link
        href="/profile#pricingSectian"
        className="mt-6 px-6 py-3 bg-yellow-600 text-white rounded-lg shadow hover:bg-yellow-700 transition"
      >
        {t('tryAgain')}
      </Link>
    </div>
  );
}
