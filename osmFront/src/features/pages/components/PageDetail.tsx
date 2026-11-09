'use client';
import { useEffect, useState } from "react";
import { Loading4 } from "@/src/shared/components/ui/loding";
import { Card, CardContent, CardHeader, CardTitle } from "@/src/shared/components/ui/card";
import { RenderButtons } from "@/src/shared/components/ui/buttons/RenderButtons";
import { useCallback } from "react";
import {useTranslations} from 'next-intl';
import {useLocale} from 'next-intl';
import {useApiForm} from '@/src/shared/hooks/useApiForm';
export const PageDetail = ({ pageId }: { pageId: any }) => {

  const t = useTranslations("pagesList");
  const locale = useLocale();

  const [pageData, setPageData] = useState<any>(null);

  const aliases = { deleteAlias: 'users_pages_destroy', editAlias: 'users_pages_partial_update' };


  

     const fetchPage = useApiForm({
      alias: "users_pages_retrieve",
      defaultValues: { id: pageId },
   
    });
  

  const refetch = useCallback(async () => {
    if (pageId == null) return;
    const res = await fetchPage.query.refetch();
    if (res?.status) {
      setPageData(res.data);
    }
    //  submitForm({ id: pageId });
  }, [pageId]);
  
  useEffect(() => {
    refetch();
  }, [refetch]);
  

  const translation = pageData?.translations?.find((t: any) => t.language === locale)
    || pageData?.translations?.find((t: any) => t.language === pageData.default_language);
  
    if (!pageId) return <div>No Page Found</div>;
  if (!pageData) return <Loading4 />;

  return (
    <Card className="shadow-md rounded-2xl border">
      <CardHeader>
        <CardTitle>{translation?.title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <p><b>{t('slug')}:</b> {pageData?.slug}</p>
        <p><b>{t('status')}:</b> {pageData?.is_published ? t('published'): t('draft')}</p>
        <p><b>{t('seoTitle')}:</b> {translation?.seo_title}</p>
        <p><b>{t('isDeleted')}:</b> {pageData?.is_deleted ? <span>✅</span> : <span className="text-red-700">❌</span>}</p>
        <p><b>{t('isPublished')}:</b> {pageData?.is_published ? <span>✅</span> : <span  className="text-red-700">❌</span>}</p>
        <p><b>{t('isActive')}:</b> {pageData?.is_active ? <span>✅</span> : <span  className="text-red-700">❌</span>}</p>


        <p className="text-red-500 text-sm bg-red-50">
          {pageData?.is_deleted && t('deletedMessage')}
        </p>
        <div className="prose max-w-none border-t pt-4"
          dangerouslySetInnerHTML={{ __html: translation?.content ?? "" }}
        />

        <RenderButtons data={pageData} alias={aliases} refetch={refetch} navigatePath={`/dashboard/pages/`} />
      </CardContent>
    </Card>
  );
};

