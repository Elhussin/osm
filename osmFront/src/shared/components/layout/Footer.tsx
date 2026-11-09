"use client"
import { navUrl, socialLinks, otherLinks } from "@/src/shared/constants/url"
import { Link } from "@/src/app/i18n/navigation";
import {useTranslations} from 'next-intl';
export default function Footer() {
  const t = useTranslations("footer");
  const t2 = useTranslations("aside");
  return (
    <footer className="footer">
      <div className="max-w-7xl mx-auto grid grid-cols-1 sm:grid-cols-3 gap-2 text-sm ">


        {/* Column 2: Page Links */}
        <div>
          <h4 className="text-lg font-semibold mb-4 border-b pb-2 w-1/2 ">{t("quickLinks")}</h4>
          <ul className="space-y-2">
            {navUrl.map((item, index) => (
              <li key={index}>
                <Link href={item.path} className="hover:text-primary transition">
                  {t2(item.name)}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* Column 3: Other Info */}
        <div>
          <h4 className="text-lg font-semibold mb-4 border-b pb-2 w-1/2">{t("more")}</h4>
          <ul className="space-y-2">
            {otherLinks.map((item, index) => (
              <li key={index}>
                <Link href={item.path} className="hover:text-primary transition">
                  {t(item.name)}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* Column 1: Social Icons */}
        <div>
          <h4 className="text-lg font-semibold mb-4 border-b pb-2 w-1/2">{t("followUs")}</h4>
          <div className="grid grid-cols-3 gap-3  justify-around max-w-1/2">
            {socialLinks.map((item, index) => {
              const Icon = item.icon;
              return (
                <Link
                  key={index}
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  title={item.name}
                  className="flex justify-center text-gray-600 dark:text-gray-300 hover:text-primary transition"
                >
                  <Icon size={22} />
                </Link>
              );
            })}
        </div>
        </div>

      </div>

      {/* Footer bottom */}
      <div className="mt-10 text-center text-xs text-gray-500 dark:text-gray-400">
        &copy; {new Date().getFullYear()} {t("footer")}. All rights reserved.
      </div>
    </footer>
  );
}
