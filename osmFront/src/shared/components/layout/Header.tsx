// src/components/layout/Header.tsx
'use client';

import { useState, useEffect } from "react";
import ThemeToggle from "../ui/ThemeToggle";
import LocaleSwitcher from "../ui/LocaleSwitcher";
import Image from "next/image";
import { Link } from "@/src/app/i18n/navigation";
import { AsideButton } from "@/src/shared/components/ui/buttons/AsideButton";
import DesktopNavLinks from './DesktopNavLinks';
import MobileNavMenu from './MobileNavMenu';
import { AutoHideSearchOnRouteChange } from '../search/AutoHideSearchOnRouteChange';
import { getSubdomain } from '@/src/shared/utils/getSubdomain';
import { Menu, X } from 'lucide-react';
import { motion, useScroll, useMotionValueEvent } from "framer-motion";
import { useUser } from '@/src/features/auth/hooks/UserContext';
import LogoutButton from '../ui/buttons/logout';
export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [subdomain, setSubdomain] = useState<string | null>(null);
  const [hidden, setHidden] = useState(false);
  const { scrollY } = useScroll();
  const { user, logout } = useUser();

  useEffect(() => {
    setSubdomain(getSubdomain());
  }, []);

  useMotionValueEvent(scrollY, "change", (latest) => {
    const previous = scrollY.getPrevious() || 0;
    if (latest > previous && latest > 150) {
      setHidden(true);
    } else {
      setHidden(false);
    }
  });

  return (
    <motion.header
      variants={{
        visible: { y: 0 },
        hidden: { y: "-100%" },
      }}
      animate={hidden ? "hidden" : "visible"}
      transition={{ duration: 0.35, ease: "easeInOut" }}
      className="fixed top-0 z-40 w-full border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-950/80 backdrop-blur-md supports-[backdrop-filter]:bg-white/60 dark:supports-[backdrop-filter]:bg-gray-950/60"
    >
      <AutoHideSearchOnRouteChange />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between gap-4">

          {/* Logo & Aside Toggle */}
          <div className="flex shrink-0 items-center gap-2">
            <AsideButton />
            <Link href="/" className="flex items-center gap-2 group transition-opacity hover:opacity-90">
              <div className="relative overflow-hidden rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm">
                <Image
                  className="bg-amber-100 dark:bg-amber-900/20 object-cover"
                  src="/media/logo.png"
                  alt="OSM Logo"
                  width={40}
                  height={40}
                  priority
                  title="O-S-M Optics Store Management"
                />
              </div>
              <span className="hidden font-bold text-lg  tracking-tight text-gray-900 dark:text-gray-100 sm:block">
                OSM
              </span>
            </Link>
          </div>

          {/* Desktop Navigation (Center) */}
          <div className="hidden md:flex flex-1 justify-center">
            <DesktopNavLinks subdomain={subdomain} />
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-2 sm:gap-3">
            <LocaleSwitcher />
            <ThemeToggle />
            <div className="hidden md:block">
            {user && <LogoutButton logout={logout}/>}
            </div>

            {/* Mobile Menu Toggle */}
            <div className="md:hidden">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="p-2 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 rounded-md focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500"
              >
                <span className="sr-only">Open main menu</span>
                {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            </div>
          </div>
        </div>
      </div>

      <MobileNavMenu isMenuOpen={isMenuOpen} setIsMenuOpen={setIsMenuOpen} subdomain={subdomain} />
    </motion.header>
  );
}
