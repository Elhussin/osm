"use client";
import {contact } from "@/src/shared/constants/conteact";
import {socialLinks } from "@/src/shared/constants/url";
import { useTranslations } from "next-intl";
import {Link} from "@/src/app/i18n/navigation"
export default  function ContactPage() {
  const t =  useTranslations("contact");

  return (
    <div className="max-w-5xl mx-auto mt-10 p-6 bg-white dark:bg-gray-900 rounded-xl shadow space-y-10">
      <h1 className="text-3xl font-bold text-center text-gray-900 dark:text-white">
        {t("title")}
      </h1>

      <div className="grid md:grid-cols-2 gap-8">
        {/* Left Column: Contact Info */}
        <div className="space-y-6 text-gray-700 dark:text-gray-200">
          <p>{t("description")}</p>

          <div>
            <p><strong>{t("company")}:</strong> {contact.companyName}</p>
            <p><strong>{t("email")}:</strong> <a href={`mailto:${contact.email}`} className="text-blue-600">{contact.email}</a></p>
            <p><strong>{t("phone")}:</strong> <a href={`tel:${contact.phone}`} className="text-blue-600">{contact.phone}</a></p>
            <p><strong>{t("address")}:</strong> {contact.address}</p>
          </div>

          <div className="flex flex-wrap gap-4 pt-4">
            {socialLinks.map(({ url, icon: Icon, name }) => (
              <Link key={name} href={url} target="_blank" title={name} className="text-xl hover:text-blue-600 transition">
                <Icon aria-label={name} />
              </Link>
            ))}
          </div>
        </div>
        </div>
      </div>

  );
}
