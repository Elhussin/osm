"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import RichTextEditor from "./RichTextEditor";
import {
  CreatePageData,
  Language,
  PageTranslation,
  LANGUAGES,
} from "@/src/features/pages/types";
import { safeToast } from "@/src/shared/utils/safeToast";
import { Loading4 } from "@/src/shared/components/ui/loding";
import { defaultPublicPages } from "@/src/shared/constants/defaultPublicPages";
import { useTranslations } from "next-intl";
import { useLocale } from "next-intl";
import { getBaseUrl } from "@/src/shared/utils/getBaseUrl";
import { useApiForm } from "@/src/shared/hooks/useApiForm";
interface MultilingualPageEditorProps {
  pageId?: string;
  defaultPage?: string | null;
}
type FormError = {
  message: string;
};

const MultilingualPageEditor: React.FC<MultilingualPageEditorProps> = ({
  pageId,
  defaultPage,
}) => {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [activeLanguage, setActiveLanguage] = useState<Language>("en");
  const t = useTranslations("MultilingualPageEditor");
  const locale = useLocale();
  const [formErrors, setFormErrors] = useState<{ [key: string]: FormError }>(
    {}
  );

  const [formData, setFormData] = useState<CreatePageData | null>(null);

  const pageRequest = useApiForm({
    alias: `users_pages_retrieve`,
    defaultValues: { id: pageId },
  });
  const createRequest = useApiForm({ alias: `users_pages_create` });
  const updateRequest = useApiForm({
    alias: `users_pages_partial_update`,
    onSuccess: () => {
      safeToast(t("PageUpdated"), { type: "success" });
      loadPage();
    },
    onError: () => {
      safeToast(t("errorUpdatingPage"), { type: "error" });
    },
  });

  // دالة لتوليد slug من العنوان
  const generateSlug = (title: string) => {
    return title
      .toLowerCase()
      .replace(/[^a-z0-9 -]/g, "")
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-")
      .trim();
  };

  // تحديث ترجمة محددة
  const updateTranslation = (
    language: Language,
    field: keyof PageTranslation,
    value: string
  ) => {
    setFormData((prev) => {
      if (!prev) return prev;

      return {
        ...prev,
        translations: prev.translations.map((t) => {
          if (t.language === language) {
            const updated = { ...t, [field]: value };
            if (field === "title") {
              updated.seo_title = value;
            }
            return updated;
          }
          return t;
        }),
      };
    });
  };

  // الحصول على الترجمة الحالية للغة النشطة
  const getCurrentTranslation = () => {
    if (!formData) return null;
    return (
      formData.translations.find((t) => t.language === activeLanguage) ||
      formData.translations[0]
    );
  };

  const getTranslationCompleteness = (language: Language) => {
    if (!formData) return 0;

    const translation = formData.translations.find(
      (t) => t.language === language
    );
    if (!translation) return 0;

    const fields = ["title", "content", "seo_title"];
    const completedFields = fields.filter((field) =>
      translation[field as keyof PageTranslation]?.toString().trim()
    );
    return Math.round((completedFields.length / fields.length) * 100);
  };

  useEffect(() => {
    if (defaultPage) {
      const def = defaultPublicPages[defaultPage];
      if (def) {
        setFormData({
          default_language: def.default_language || "en",
          translations: Object.entries(LANGUAGES).map(([code]) => {
            const existing = def.translations.find((t) => t.language === code);
            return (
              existing || {
                language: code as Language,
                title: "",
                content: "",
                seo_title: "",
                meta_description: "",
                meta_keywords: "",
              }
            );
          }),
          is_published: def.is_published || false,
          slug: def.slug || "",
        });
      }
    } else if (!pageId) {
      setFormData({
        default_language: "en",
        translations: Object.entries(LANGUAGES).map(([code]) => ({
          language: code as Language,
          title: "",
          content: "",
          seo_title: "",
          meta_description: "",
          meta_keywords: "",
        })),
        is_published: false,
        slug: "",
      });
    }
  }, [pageId]);
  // defaultPage

  const loadPage = useCallback(async () => {
    try {
      setLoading(true);
      const res = await pageRequest.query.refetch();
      const page = res.data;

      // تأكد من وجود جميع اللغات المطلوبة
      const translations = Object.entries(LANGUAGES).map(([code]) => {
        const existing = page.translations.find(
          (t: PageTranslation) => t.language === code
        );
        return (
          existing || {
            language: code as Language,
            title: "",
            content: "",
            seo_title: "",
            meta_description: "",
            meta_keywords: "",
          }
        );
      });

      setFormData({
        ...page,
        translations,
      });
      setActiveLanguage(page.default_language);
    } catch (error) {
      safeToast(t("errorLoading"), { type: "error" });
    } finally {
      setLoading(false);
    }
  }, [pageId]);

  useEffect(() => {
    if (pageId) {
      loadPage();
    }
  }, [pageId]);

  const handleSave = async () => {
    try {
      setSaving(true);

      if (!formData) {
        safeToast(t("errorGetFormData"), { type: "error" });
        return;
      }
      // await updatePrescriptionApi.mutation.mutateAsync(data);
      // التحقق من وجود عنوان للغة الافتراضية
      const defaultTranslation = formData.translations.find(
        (t) => t.language === formData.default_language
      );
      if (!defaultTranslation?.title.trim()) {
        safeToast(
          `${t("pleaseProvideTitle")} (${
            LANGUAGES[formData.default_language].name
          })`,
          { type: "error" }
        );
        return;
      }

      // توليد slug للصفحات الجديدة فقط
      const finalFormData = { ...formData };
      if (!pageId && !finalFormData.slug.trim()) {
        finalFormData.slug = generateSlug(defaultTranslation.title);
      }

      let result;
      if (pageId) {
        result = await updateRequest.mutation.mutateAsync({
          id: pageId,
          formData: finalFormData,
        });
        setFormData(result.data);
      } else {
        result = await createRequest.submitForm(finalFormData);
        if (result?.success) {
          safeToast(t("PageCreated"), { type: "success" });
        } else {
          setFormErrors(createRequest.errors || {});
          safeToast(t("errorCreatingPage"), { type: "error" });
        }
      }
    } catch (error) {
      safeToast(t("errorSavingPage"), { type: "error" });
    } finally {
      setSaving(false);
    }
  };

  const baseUrl = getBaseUrl();
  if (loading || !formData) {
    return <Loading4 />;
  }

  const currentTranslation = getCurrentTranslation();
  const currentLangInfo = LANGUAGES[activeLanguage];

  if (!currentTranslation) {
    return <div>{t("noTranslationFound")}</div>;
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-surface rounded-lg shadow-lg">
        {/* Header with language tabs */}
        <div className="border-b border-gray-200 p-6">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-2xl font-bold">
              {pageId ? t("editPage") : t("createNewPage")}
            </h1>

            {/* Default Language Selector */}
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">
                {t("defaultLanguage")}:
              </label>
              <select
                value={formData.default_language}
                onChange={(e) =>
                  setFormData((prev) =>
                    prev
                      ? {
                          ...prev,
                          default_language: e.target.value as Language,
                        }
                      : prev
                  )
                }
                className="px-3 py-1 border border-gray-300 rounded-md text-sm"
              >
                {Object.entries(LANGUAGES).map(([code, lang]) => (
                  <option className="bg-surface" key={code} value={code}>
                    {lang.flag} {lang.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Language Tabs */}
          <div className="flex space-x-1">
            {Object.entries(LANGUAGES).map(([code, lang]) => {
              const completeness = getTranslationCompleteness(code as Language);
              const isActive = activeLanguage === code;
              return (
                <button
                  key={code}
                  onClick={() => setActiveLanguage(code as Language)}
                  className={`px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors ${
                    isActive
                      ? "bg-blue-50 text-blue-700 border-blue-500"
                      : "bg-gray-50 text-gray-700 border-transparent hover:bg-gray-100"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span>{lang.flag}</span>
                    <span>{lang.name}</span>
                    {formData.default_language === code && (
                      <span className="text-xs bg-green-100 text-green-800 px-1 rounded">
                        {t("default")}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {completeness}% {t("complete")}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Page URL Field */}
          <div className="mt-4">
            <label className="block font-medium">{t("pageURL")}</label>
            <span className="text-xs text-gray-500 mt-1">
              {t("pageURLDesc")}
            </span>

            <input
              type="text"
              title={t("pageURLDesc")}
              value={pageId ? `${baseUrl}/${formData.slug}` : formData.slug}
              onChange={(e) => {
                if (!pageId) {
                  setFormData((prev) =>
                    prev ? { ...prev, slug: e.target.value } : prev
                  );
                }
              }}
              disabled={!!pageId}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              placeholder={t("pageURLDesc")}
              dir={currentLangInfo.dir}
            />
            {formErrors?.slug?.message && (
              <p className="text-red-500 text-sm mt-1">
                {formErrors.slug.message}
              </p>
            )}
          </div>
        </div>

        {/* Content for active language */}
        <div
          className={`p-6 ${locale === "ar" ? "text-right" : "text-left"}`}
          dir={locale === "ar" ? "rtl" : "ltr"}
        >
          <div className="space-y-6">
            {/* Basic Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t("pageTitle")} ({currentLangInfo.name})
                </label>
                <input
                  type="text"
                  title={t("pageTitleDesc")}
                  value={currentTranslation.title}
                  onChange={(e) =>
                    updateTranslation(activeLanguage, "title", e.target.value)
                  }
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={`${t("pageTitleDesc")} ${currentLangInfo.name}`}
                  dir={currentLangInfo.dir}
                />
                {formErrors?.title && (
                  <p className="text-red-500 text-sm mt-1">
                    {formErrors.title.message as string}
                  </p>
                )}
              </div>
            </div>

            {/* Content Editor */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t("content")} ({currentLangInfo.name})
              </label>
              {activeLanguage === "en" && (
                <RichTextEditor
                  content={currentTranslation.content}
                  onChange={(content) =>
                    updateTranslation(activeLanguage, "content", content)
                  }
                  language={activeLanguage}
                  placeholder={`${t("contentDesc")} ${currentLangInfo.name}...`}
                />
              )}
              {activeLanguage === "ar" && (
                <RichTextEditor
                  content={currentTranslation.content}
                  onChange={(content) =>
                    updateTranslation(activeLanguage, "content", content)
                  }
                  language={activeLanguage}
                  placeholder={`${t("contentDesc")} ${currentLangInfo.name}...`}
                />
              )}
              {formErrors?.content && (
                <p className="text-red-500 text-sm mt-1">
                  {formErrors.content.message as string}
                </p>
              )}
            </div>

            {/* SEO Fields */}
            <div className="border-t pt-6">
              <h3 className="text-lg font-semibold mb-4">
                {t("seoSettings")} ({currentLangInfo.name})
              </h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t("seoTitle")}
                  </label>
                  <input
                    type="text"
                    title={t("seoTitleDesc")}
                    value={currentTranslation.seo_title}
                    onChange={(e) =>
                      updateTranslation(
                        activeLanguage,
                        "seo_title",
                        e.target.value
                      )
                    }
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder={`${t("seoTitleDesc")} ${currentLangInfo.name}`}
                    dir={currentLangInfo.dir}
                  />
                  {formErrors?.seo_title && (
                    <p className="text-red-500 text-sm mt-1">
                      {formErrors.seo_title.message as string}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t("metaDescription")}
                  </label>
                  <textarea
                    title={t("metaDescriptionDesc")}
                    value={currentTranslation.meta_description}
                    onChange={(e) =>
                      updateTranslation(
                        activeLanguage,
                        "meta_description",
                        e.target.value
                      )
                    }
                    rows={3}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder={t("metaDescription")}
                    dir={currentLangInfo.dir}
                  />
                  {formErrors?.meta_description && (
                    <p className="text-red-500 text-sm mt-1">
                      {formErrors.meta_description.message as string}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t("metaKeywords")}
                  </label>
                  <input
                    type="text"
                    title={t("metaKeywordsDesc")}
                    value={currentTranslation.meta_keywords}
                    onChange={(e) =>
                      updateTranslation(
                        activeLanguage,
                        "meta_keywords",
                        e.target.value
                      )
                    }
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder={`keyword1, keyword2, keyword3, ${t(
                      "metaKeywordsDesc"
                    )}`}
                    dir={currentLangInfo.dir}
                  />
                  {formErrors.meta_keywords && (
                    <p className="text-red-500 text-sm mt-1">
                      {formErrors.meta_keywords.message as string}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Publication Settings */}
            <div className="border-t pt-6">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_published"
                  checked={formData.is_published}
                  onChange={(e) =>
                    setFormData((prev) =>
                      prev ? { ...prev, is_published: e.target.checked } : prev
                    )
                  }
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label
                  htmlFor="is_published"
                  className="ml-2 text-sm font-medium text-gray-700"
                >
                  {t("publish")}
                </label>
              </div>
              {formErrors.root && (
                <p className="error-text">
                  {formErrors.root.message as string}
                </p>
              )}
            </div>

            {/* Actions */}
            <div className="flex justify-between pt-6 border-t">
              <button
                onClick={() => router.back()}
                className="px-6 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                {t("cancel")}
              </button>

              <button
                onClick={handleSave}
                disabled={saving || !currentTranslation.title.trim()}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {saving
                  ? `${t("save")}... `
                  : pageId
                  ? `${t("update")}`
                  : `${t("create")}`}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MultilingualPageEditor;
