// app/unauthorized/page.tsx
'use client';
import { ShieldX } from 'lucide-react';
import { redirect, useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { generateMetadata } from '@/src/shared/utils/metadata';
generateMetadata({
  title: 'Unauthorized | O-S-M',
  description: 'You do not have permission to access this page.',
  keywords: ['optical', 'system', 'management', 'O-S-M'],
  openGraphType: 'unauthorized',
  twitterCardType: 'summary',
});

export default function UnauthorizedPage() {
  const router = useRouter();
  const t = useTranslations('unauthorized');

  useEffect(() => {
    // إعادة التوجيه التلقائي بعد 3 ثواني
    const timer = setTimeout(() => {
      router.push('/');
      redirect('/');
    }, 3000);

    return () => clearTimeout(timer);
  }, [router]);

  return (
    <div className="flex items-center justify-center">
      <div className="max-w-md w-full bg-surface shadow-lg rounded-lg p-8 text-center">
        <div className="mb-4">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
            <ShieldX className="h-6 w-6 text-red-600"/>
          </div>
        </div>
        
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          {t('title')}
        </h1>
        
        <p className="text-gray-600 mb-6">
          {t('message')}
        </p>
        
        <div className="space-y-3">
          <button
            onClick={() => router.back()}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition duration-200"
          >
            {t('backButton')}
          </button>
          
          <button
            onClick={() => router.push('/')}
            className="w-full bg-gray-200 text-gray-800 py-2 px-4 rounded-md hover:bg-gray-300 transition duration-200"
          >
            {t('homeButton')}
          </button>
        </div>
        
        <p className="text-sm text-gray-500 mt-4">
          {t('redirectMessage')}
        </p>
      </div>
    </div>
  );
}
