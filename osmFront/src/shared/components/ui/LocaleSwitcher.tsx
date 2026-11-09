'use client';

import { useRouter, usePathname } from '@/src/app/i18n/navigation';
import { useLocale, useTranslations } from 'next-intl';
import { useTransition, useEffect, useState, useRef } from 'react';
import Cookies from 'js-cookie';
import { languages, countries, currencies, currencyMap } from '@/src/shared/constants';
import { Loader2, Globe, ChevronDown, Check, MapPin, Coins } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import { useClickOutside } from '@/src/shared/hooks/useClickOutside';
// C:\coding\optics_tenant\osmFront\src\shared\hooks\useClickOutside.tsx
type Tab = 'language' | 'country' | 'currency';

export default function LocaleSwitcher() {
  const router = useRouter();
  const pathname = usePathname();
  const locale = useLocale();
  // const t = useTranslations('common'); // Assuming you have common translations, or use fallback text

  const [isPending, startTransition] = useTransition();
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('language');
  const dropdownRef = useRef<HTMLDivElement>(null);

  useClickOutside(dropdownRef, () => setIsOpen(false));

  const defaultLanguage = process.env.DEFAULT_LANGUAGE || 'en';
  const defaultCountry = process.env.DEFAULT_COUNTRY || 'sa';
  const defaultCurrency = process.env.DEFAULT_CURRENCY || 'sar';

  const [country, setCountry] = useState(Cookies.get('country') || defaultCountry);
  const [currency, setCurrency] = useState(Cookies.get('currency') || defaultCurrency);

  // Sync state (simplified for UI)
  useEffect(() => {
    if (!Cookies.get('country')) handleAutoDetect();
  }, []);

  const handleAutoDetect = async () => {
    try {
      const res = await fetch('https://ipapi.co/json/');
      const data = await res.json();
      const detected = data.country_code?.toLowerCase();
      if (detected) {
        const matched = countries.find(c => c.value === detected);
        if (matched) {
          setCountry(matched.value);
          setCurrency(currencyMap[matched.value] || defaultCurrency);
          Cookies.set('country', matched.value, { path: '/', expires: 30 });
          Cookies.set('currency', currencyMap[matched.value] || defaultCurrency, { path: '/', expires: 30 });
        }
      }
    } catch (e) { console.error("Auto detect failed", e); }
  };

  const handleLanguageChange = (newLang: string) => {
    if (newLang !== locale) {
      startTransition(() => {
        router.replace(pathname, { locale: newLang });
        setIsOpen(false);
      });
    }
  };

  const handleCountryChange = (selected: string) => {
    setCountry(selected);
    const newCurr = currencyMap[selected] || defaultCurrency;
    setCurrency(newCurr);
    Cookies.set('country', selected, { path: '/', expires: 30 });
    Cookies.set('currency', newCurr, { path: '/', expires: 30 });
  };

  const handleCurrencyChange = (selected: string) => {
    setCurrency(selected);
    Cookies.set('currency', selected, { path: '/', expires: 30 });
  };

  const activeLanLabel = languages.find(l => l.value === locale)?.label.substring(0, 3).toUpperCase();

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors border border-transparent hover:border-gray-200 dark:hover:border-gray-700"
      >
        <Globe size={18} className="text-gray-500" />
        <span>{activeLanLabel}</span>
        <span className="w-px h-4 bg-gray-300 dark:bg-gray-600 mx-1" />
        <span className="uppercase text-xs text-gray-500">{country}</span>
        {isPending ? <Loader2 size={14} className="animate-spin ml-1" /> : <ChevronDown size={14} className={clsx("transition-transform duration-200", isOpen && "rotate-180")} />}
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute right-0 top-full mt-2 w-80 bg-white dark:bg-gray-900 rounded-xl shadow-xl border border-gray-200 dark:border-gray-800 p-4 z-50 origin-top-right"
          >
            {/* Tabs */}
            <div className="flex p-1 mb-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
              {(['language', 'country', 'currency'] as Tab[]).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={clsx(
                    "flex-1 flex items-center justify-center py-1.5 text-xs font-medium rounded-md transition-all",
                    activeTab === tab
                      ? "bg-white dark:bg-gray-700 text-primary-600 dark:text-primary-400 shadow-sm"
                      : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  )}
                >
                  {tab === 'language' && <Globe size={12} className="mr-1.5" />}
                  {tab === 'country' && <MapPin size={12} className="mr-1.5" />}
                  {tab === 'currency' && <Coins size={12} className="mr-1.5" />}
                  <span className="capitalize">{tab}</span>
                </button>
              ))}
            </div>

            {/* Content */}
            <div className="space-y-1 max-h-60 overflow-y-auto scrollbar-thin px-1">

              {activeTab === 'language' && languages.map((l) => (
                <button
                  key={l.value}
                  onClick={() => handleLanguageChange(l.value)}
                  className={clsx(
                    "w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors",
                    locale === l.value
                      ? "bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400"
                      : "hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-200"
                  )}
                >
                  <span className="flex items-center gap-2">
                    <span className="text-lg">{l.label.split(' ')[0]}</span> {/* Assuming first part is flag/emoji if present, else just label */}
                    {l.label}
                  </span>
                  {locale === l.value && <Check size={16} />}
                </button>
              ))}

              {activeTab === 'country' && countries.map((c) => (
                <button
                  key={c.value}
                  onClick={() => handleCountryChange(c.value)}
                  className={clsx(
                    "w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors",
                    country === c.value
                      ? "bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400"
                      : "hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-200"
                  )}
                >
                  <span className="flex items-center gap-2">
                    {c.label}
                  </span>
                  {country === c.value && <Check size={16} />}
                </button>
              ))}

              {activeTab === 'currency' && currencies.map((c) => (
                <button
                  key={c.value}
                  onClick={() => handleCurrencyChange(c.value)}
                  className={clsx(
                    "w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors",
                    currency === c.value
                      ? "bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400"
                      : "hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-200"
                  )}
                >
                  <span className="flex items-center gap-2">
                    {c.label}
                  </span>
                  {currency === c.value && <Check size={16} />}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
