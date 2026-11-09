'use client';
import { Link } from '@/src/app/i18n/navigation';
import { useUser } from '@/src/features/auth/hooks/UserContext';
import LogoutButton from '../ui/buttons/logout';
import { useTranslations } from 'next-intl';
import { useSearch } from "@/src/shared/contexts/SearchContext";
import { Search, X } from "lucide-react";
import { ActionButton } from "../ui/buttons";
import { useSearchButton } from "@/src/shared/contexts/SearchButtonContext";
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import clsx from 'clsx';

export default function DesktopNavLinks({ subdomain }: { subdomain: string | null }) {
  const { user } = useUser();
  const t = useTranslations('navBar');
  const { toggleSearch, isSearchVisible } = useSearch();
  const { isVisible } = useSearchButton();
  const pathname = usePathname();


  const NavItem = ({ href, children }: { href: string; children: React.ReactNode }) => {
    const isActive = pathname === href || (href !== '/' && pathname?.startsWith(href));

    return (
      <Link href={href} className="relative px-3 py-1.5 text-sm font-medium transition-colors text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100">
        {isActive && (
          <motion.span
            layoutId="nav-pill"
            className="absolute inset-0 z-[-1] rounded-md bg-gray-100 dark:bg-gray-800"
            transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
          />
        )}
        <span className={clsx("relative z-10", isActive && "text-primary-600 dark:text-primary-400")}>
          {children}
        </span>
      </Link>
    );
  };

  return (
    <div className="hidden md:flex gap-6 items-center justify-between w-full">
      {/* Navigation Links */}
      <div className="flex gap-2 items-center">
        <NavItem href="/">{t('home')}</NavItem>
        {user && user.role === 'ADMIN' && <NavItem href="/admin">{t('admin')}</NavItem>}
        {user && user.role === 'TECHNICIAN' && <NavItem href="/prescriptions">{t('technician')}</NavItem>}
        {user && <NavItem href="/profile">{t('profile')}</NavItem>}
      </div>

      {/* Search and Auth Actions */}
      <div className="flex gap-3 items-center">
        {user ? (
          <>
            {isVisible && (
              <ActionButton
                onClick={toggleSearch}
                type="button"
                variant="link"
                className="hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 hover:text-gray-900 dark:text-gray-400"
                icon={isSearchVisible ? <X className="h-4 w-4 text-red-500" /> : <Search className="h-4 w-4" />}
                title={isSearchVisible ? t('closeSearch') : t('search')}
              />
            )}
          </>
        ) : (
          <div className="flex items-center gap-3">
            <Link href="/auth/login" className="text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors">{t('login')}</Link>
            <Link href="/auth/register" className="px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary-700 rounded-lg shadow-sm transition-all">{t('register')}</Link>
          </div>
        )}
      </div>
    </div>
  );
}
