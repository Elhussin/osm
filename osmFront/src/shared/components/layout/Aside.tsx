'use client';
import { useAside } from '@/src/shared/contexts/AsideContext';
import React from 'react';
import { Link } from '@/src/app/i18n/navigation';
import { motion, AnimatePresence } from "framer-motion";
import { useUser } from '@/src/features/auth/hooks/UserContext';
import { X } from 'lucide-react';
import { URLDATA, navUrl } from '@/src/shared/constants/url';
import Image from 'next/image';
import { useTranslations, useLocale } from 'next-intl';
import { usePathname } from 'next/navigation';
import {
  Home, Shield, Eye, User, Users, Building2,
  BarChart3, Truck, Phone, Info, LogIn, UserPlus, Grid
} from 'lucide-react';
import clsx from 'clsx';

export default function Aside() {
  const locale = useLocale();
  const isRTL = locale === 'ar';

  const { isVisible, asideContent, toggleAside } = useAside();

  return (
    <>
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.5 }}
            exit={{ opacity: 0 }}
            onClick={toggleAside}
            className="fixed inset-0 bg-black/50 z-40 md:hidden"
          />
        )}
      </AnimatePresence>

      <motion.aside
        initial={{ x: isRTL ? '100%' : '-100%' }}
        animate={{ x: isVisible ? '0%' : isRTL ? '100%' : '-100%' }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className={`fixed top-0 ${isRTL ? 'right-0 border-l' : 'left-0 border-r'} h-full w-80 bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-800 shadow-xl z-50 overflow-hidden flex flex-col`}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-100 dark:border-gray-800">
          <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">Menu</span>
          <button
            onClick={toggleAside}
            className="p-2 text-gray-500 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {asideContent ? asideContent : <AsidDeafualtContent />}
        </div>
      </motion.aside>
    </>
  );
}


const AsidDeafualtContent = () => {
  const t = useTranslations('aside');
  const { user } = useUser();
  const pathname = usePathname();

  // Helper to get icon based on path (simple mapping)
  const getIcon = (path: string) => {
    switch (path) {
      case '/': return <Home size={20} />;
      case '/admin': return <Shield size={20} />;
      case '/prescriptions': return <Eye size={20} />; // Or FileText
      case '/profile': return <User size={20} />;
      case '/users': return <Users size={20} />;
      case '/tenants': return <Building2 size={20} />;
      case '/groups': return <Users size={20} />;
      case '/crm': return <BarChart3 size={20} />;
      case '/products/supplier': return <Truck size={20} />;
      case '/contact': return <Phone size={20} />;
      case '/about': return <Info size={20} />;
      case '/auth/login': return <LogIn size={20} />;
      case '/auth/register': return <UserPlus size={20} />;
      default: return <Grid size={20} />;
    }
  };

  const NavItem = ({ item }: { item: { path: string, name: string } }) => {
    const isActive = pathname === item.path;
    return (
      <Link
        href={item.path}
        className={clsx(
          "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group",
          isActive
            ? "bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400 font-medium"
            : "text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-200"
        )}
      >
        <span className={clsx("transition-transform group-hover:scale-110", isActive && "text-primary-600 dark:text-primary-500")}>
          {getIcon(item.path)}
        </span>
        <span>{t(item.name)}</span>
        {isActive && (
          <motion.div
            layoutId="active-sidebar"
            className="ml-auto w-1.5 h-1.5 rounded-full bg-primary-600 dark:bg-primary-500"
          />
        )}
      </Link>
    );
  };

  return (
    <nav className="flex flex-col gap-1.5">
      {user ? (
        <>
          <div className="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">Dashboard</div>
          {URLDATA.map((item) => (
            <NavItem key={item.path} item={item} />
          ))}
        </>
      ) : (
        <>
          {navUrl.map((item) => (
            <NavItem key={item.path} item={item} />
          ))}
          <div className="mt-8 p-6 rounded-2xl bg-gradient-to-br from-primary-50 to-primary-100 dark:from-gray-800 dark:to-gray-900 flex flex-col items-center text-center">
            <Image src="/media/aside.png" alt="logo" width={120} height={60} className="mb-3 drop-shadow-sm" />
            <p className="text-xs text-gray-500 dark:text-gray-400">Optics Store Management</p>
          </div>
        </>
      )}
    </nav>
  );
}


