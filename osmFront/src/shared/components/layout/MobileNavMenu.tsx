'use client';
import { Link } from '@/src/app/i18n/navigation';
import { useUser } from '@/src/features/auth/hooks/UserContext';
import LogoutButton from '../ui/buttons/logout';
import { useTranslations } from 'next-intl';
import { useSearch } from "@/src/shared/contexts/SearchContext";
import { ActionButton } from "../ui/buttons";
import { Search, X } from "lucide-react";
import { useSearchButton } from "@/src/shared/contexts/SearchButtonContext";
import { AnimatePresence, motion } from "framer-motion";

export default function MobileNavMenu({ isMenuOpen, setIsMenuOpen, subdomain }: {
  isMenuOpen: boolean,
  setIsMenuOpen: (val: boolean) => void,
  subdomain: string | null
}) {
  const { user, logout } = useUser();
  const { toggleSearch, isSearchVisible } = useSearch();
  const { isVisible } = useSearchButton();
  const t = useTranslations('navBar');

  return (
    <AnimatePresence>
      {isMenuOpen && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.2 }}
          className="md:hidden overflow-hidden border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950"
        >
          <div className="flex flex-col p-4 space-y-4">
            <Link href="/" onClick={() => setIsMenuOpen(false)} className="block px-3 py-2 text-base font-medium text-gray-700 hover:text-primary-600 dark:text-gray-200 dark:hover:text-primary-400 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">{t('home')}</Link>

            {user ? (
              <>
                {user.role === 'ADMIN' && <Link href="/admin" onClick={() => setIsMenuOpen(false)} className="block px-3 py-2 text-base font-medium text-gray-700 hover:text-primary-600 dark:text-gray-200 dark:hover:text-primary-400 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">{t('admin')}</Link>}
                {user.role === 'TECHNICIAN' && <Link href="/prescriptions" onClick={() => setIsMenuOpen(false)} className="block px-3 py-2 text-base font-medium text-gray-700 hover:text-primary-600 dark:text-gray-200 dark:hover:text-primary-400 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">{t('technician')}</Link>}
                <Link href="/profile" onClick={() => setIsMenuOpen(false)} className="block px-3 py-2 text-base font-medium text-gray-700 hover:text-primary-600 dark:text-gray-200 dark:hover:text-primary-400 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">{t('profile')}</Link>
                <div className="flex items-center gap-4 px-3 pt-2">
                  {isVisible && (
                    <button
                      onClick={() => { toggleSearch(); setIsMenuOpen(false); }}
                      className="flex items-center gap-2 text-gray-600 dark:text-gray-400"
                    >
                      {isSearchVisible ? <X size={20} /> : <Search size={20} />}
                      <span>{isSearchVisible ? t('closeSearch') : t('search')}</span>
                    </button>
                  )}
                  <LogoutButton logout={() => { setIsMenuOpen(false); logout(); }} />
                </div>
              </>
            ) : (
              <div className="flex flex-col gap-3 px-3">
                {subdomain && <Link href="/auth/login" onClick={() => setIsMenuOpen(false)} className="text-gray-700 dark:text-gray-200 font-medium">{t('login')}</Link>}
                <Link href="/auth/register" onClick={() => setIsMenuOpen(false)} className="w-full text-center py-2.5 rounded-lg bg-primary text-white font-medium shadow-sm hover:bg-primary-700 transition-colors">{t('register')}</Link>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
