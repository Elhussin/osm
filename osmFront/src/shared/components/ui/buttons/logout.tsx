"use client";
import { ActionButton } from ".";
import { useTranslations } from 'next-intl';
import { LogOut } from "lucide-react";
export default function LogoutButton({ logout }: { logout: () => void }) {

  const t = useTranslations('userContext');
  return (
    <button onClick={logout} title={t('title')} className="text-secondary hover:text-red-500 transition-colors duration-200 ease-in-out cursor-pointer">
      <LogOut size={18} />
    </button>
  );
}
