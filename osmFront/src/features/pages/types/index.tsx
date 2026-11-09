export type Language = 'en' | 'ar';

export interface PageTranslation {
  language: Language;
  title: string;
  content: string;
  seo_title: string;
  meta_description: string;
  meta_keywords: string;
}

export interface PageData {
  id: number;
  tenant: string;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
  is_active: boolean;
  translations: PageTranslation[];
  default_language: Language;
  is_published: boolean;
  slug: string;
}

export interface CreatePageData {
  default_language: Language;
  translations: PageTranslation[];
  slug: string;
  is_published?:boolean;
}


export const LANGUAGES = {
  en: { name: 'English', dir: 'ltr', flag: '🇺🇸' },
  ar: { name: 'العربية', dir: 'rtl', flag: '🇸🇦' }
} as const;



export interface DefaultPublicPage {
    default_language: Language;
    translations: PageTranslation[];
    is_published: boolean;
    slug: string;
   
}