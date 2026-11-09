"use client";
import {useParams } from 'next/navigation';
import PublicPageViews from '@/src/features/pages/components/PublicPageViews';


export default  function MultilingualPublicPage() {
  const params = useParams();
  const slug = params?.slug as string;
  const locale = params?.locale as string;
  return <PublicPageViews slug={slug} locale={locale} />;
}
