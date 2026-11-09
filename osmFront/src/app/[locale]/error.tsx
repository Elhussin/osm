'use client';
import { useEffect } from 'react';
import {useTranslations} from 'next-intl';
import {Link} from '@/src/app/i18n/navigation';
import {useRouter} from '@/src/app/i18n/navigation';

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  const t = useTranslations('error');
  const redirectPath = '/';
  const routuer =useRouter();
    
  // useEffect(() => {
  //   setTimeout(() => {
  //     routuer.push(redirectPath);
  //   }, 3000);
  //   console.error('Error:', error);
  // }, [error, routuer]);

  return (
    <div className="text-center p-10">
      <h1 className="text-3xl font-bold text-red-500">{t('title')}</h1>
      <span className="text-red-500 text-xl">{error.message}</span>
      <p className="mt-4">{t('message')}</p>
      <p className="mt-2">{t('redirectMessage')}</p>

      <button
        className="mt-4 px-4 py-2 rounded"
      >
        <Link href="/" className='btn btn-primary max-w-2xl'>{t('homeButton')}</Link>
      </button>
    </div>
  );
}
