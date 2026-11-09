  // app/paypal/fail/page.tsx
  "use client";

import {Link} from '@/src/app/i18n/navigation';
import { XCircle } from "lucide-react";
import { useTranslations } from "next-intl";
export default function PayPalFailPage() {
  const t = useTranslations('paymentFail');
  return (
    <div className="min-h-screen flex flex-col justify-center items-center bg-red-50 p-6">
      <XCircle className="text-red-600 w-20 h-20 mb-4" />
      <h1 className="text-3xl font-bold text-red-700">{t('title')}</h1>
      <p className="text-gray-700 mt-2 text-center max-w-md">
        {t('description')}
      </p>
      <Link
        href="/profile"
        className="mt-6 px-6 py-3 bg-red-600 text-white rounded-lg shadow hover:bg-red-700 transition"
      >
        {t('button')}
      </Link>
    </div>
  );
}
