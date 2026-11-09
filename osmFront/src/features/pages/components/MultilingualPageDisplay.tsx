'use client';

import { PageData, Language, LANGUAGES } from '@/src/features/pages/types';
import { getCurrentTranslation } from '@/src/shared/utils/getCurrentTranslation';
import Head from 'next/head';
import { useState } from 'react';

interface MultilingualPageDisplayProps {
  page: PageData;
  defaultLanguage?: Language;
}

const MultilingualPageDisplay: React.FC<MultilingualPageDisplayProps> = ({ 
  page, 
  defaultLanguage = 'en' 
}) => {
  const [currentLanguage, setCurrentLanguage] = useState<Language>(defaultLanguage);
  const currentTranslation = getCurrentTranslation(page, currentLanguage);
  const currentLangInfo = LANGUAGES[currentLanguage];

  // Get available languages for this page
  const availableLanguages = page.translations.filter(t => 
    t.title.trim() && t.content.trim()
  );

  return (
    <>
      <Head>
        <title>{currentTranslation.seo_title || currentTranslation.title}</title>
        <meta name="description" content={currentTranslation.meta_description} />
        <meta name="keywords" content={currentTranslation.meta_keywords} />
        <meta property="og:title" content={currentTranslation.seo_title || currentTranslation.title} />
        <meta property="og:description" content={currentTranslation.meta_description} />
        <link rel="canonical" href={`/${currentLanguage}/${page.slug}`} />
        
        {/* Language alternates for SEO */}
        {availableLanguages.map(translation => (
          <link
            key={translation.language}
            rel="alternate"
            hrefLang={translation.language}
            href={`/${translation.language}/${page.slug}`}
          />
        ))}
      </Head>

      <div className="max-w-4xl mx-auto p-6" dir={currentLangInfo.dir}>

        <article className="bg-white rounded-lg shadow-lg p-8">
          <header className="mb-8">
            <h1 className={`text-4xl font-bold text-gray-900 mb-4 ${
              currentLangInfo.dir === 'rtl' ? 'text-right font-arabic' : 'text-left'
            }`}>
              {currentTranslation.title}
            </h1>
            <div className={`text-sm text-gray-500 ${
              currentLangInfo.dir === 'rtl' ? 'text-right' : 'text-left'
            }`}>
              {currentLangInfo.dir === 'rtl' 
                // ? `آخر تحديث: ${new Date(page.updated_at).toLocaleDateString('ar-SA')}`
                ? `آخر تحديث: ${new Date(page.updated_at).toLocaleDateString()}`
                : `Last updated: ${new Date(page.updated_at).toLocaleDateString()}`
              }
            </div>
          </header>

          <div 
            className={`prose prose-lg max-w-none ${
              currentLangInfo.dir === 'rtl' 
                ? 'prose-rtl text-right [&>*]:text-right' 
                : 'prose-ltr text-left'
            }`}
            dir={currentLangInfo.dir}
            dangerouslySetInnerHTML={{ __html: currentTranslation.content }}
          />
        </article>
      </div>
    </>
  );
};

export default MultilingualPageDisplay;