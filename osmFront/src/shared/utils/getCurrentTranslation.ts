import { Language, PageData, PageTranslation } from "@/src/features/pages/types";
// optics_tenant/osmFront/src/features/pages/types/index.tsx
export const getTranslation = (page: PageData, language: Language): PageTranslation | undefined => {
  return page.translations.find(t => t.language === language);
};

export const getCurrentTranslation = (page: PageData, language: Language): PageTranslation => {
  return getTranslation(page, language) || getTranslation(page, page.default_language) || page.translations[0];
};
