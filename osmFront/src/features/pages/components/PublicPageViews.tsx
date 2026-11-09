"use client";
import MultilingualPageDisplay from '@/src/features/pages/components/MultilingualPageDisplay';
import { useEffect, useState } from 'react';
import { Language } from '@/src/features/pages/types';
import { Loading4 } from '@/src/shared/components/ui/loding';
import { NotFound} from '@/src/shared/components/views/NotFound';
import { useApiForm } from '@/src/shared/hooks/useApiForm';

export default  function PublicPageViews({slug,locale}: {slug: string,locale: string}) {

  const pageRequest = useApiForm({ alias: `users_public_pages_retrieve`,defaultValues: { slug: slug } });
  const [pageData, setPageData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;  
    const fetchPage = async () => {
      try {
        const res = await pageRequest.query.refetch();
        if (res?.status) {
          setPageData(res.data);
        } else {
          setError('Page not found');

         
        }
      } catch (err) {
        setError('Error loading page');
      } finally {
        setLoading(false);
      }
    };
    fetchPage();
  }, [slug]);
// pageRequest
  if (loading) return <Loading4/>;
  if (error) {
    return (
      <>

      <NotFound error={error} />;
      </>
    )
  }
  
  return <MultilingualPageDisplay page={pageData} defaultLanguage={locale as Language} />;
}
