"use client";

import { ActionButton } from "@/src/shared/components/ui/buttons";
import { Plus } from "lucide-react";
import { useTranslations } from "next-intl";
  
export default function PublicPages() {
  const publicPages = ["about", "contact", "privacy", "terms", "faq", "support", "careers", "blog"]
  const t = useTranslations("pages");
  const t2 = useTranslations("publicPagesList");
  return (
    <div className="space-y-6">
      <div className="flex justify-end gap-2">
        {/* create Public Page */}
        <ActionButton label={t('createNewPage')} icon={<Plus size={16} />} variant="info" title={t("createNewPage")} navigateTo={"/dashboard/pages/create"} />
      </div>
      
        <>
          <h2>{t("publicPages")}</h2>
          <hr className="text-primary w-1/2"/>
          <p>{t("publicPagesDesc")}</p>
          <div className="grid gap-4 grid-cols-2 md:grid-cols-3 lg:grid-cols-4">

            {publicPages.map((page) => (
              <div className="card btn" key={page}>
                <ActionButton key={page} label={t2(page)}icon={<Plus size={16} />} variant="outline" title={`Create a new ${page.charAt(0).toUpperCase() + page.slice(1)} Page`} navigateTo={`/dashboard/pages/create?default=${page}`} />

              </div>
            ))}
          </div>
          <h2>{t("allPages")}</h2>
          <hr className="text-primary w-1/2"/>
        </>
    </div>
  );
}


