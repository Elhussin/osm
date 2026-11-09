'use client';
import { useAside } from '@/src/shared/contexts/AsideContext';
import { Menu ,X} from 'lucide-react';
import { cn } from '@/src/shared/utils/cn';

export const AsideButton = () => {
  const { isVisible, toggleAside } = useAside();

  return (
    <button
      onClick={toggleAside}
      aria-label="Toggle Sidebar"
      className= {cn("aside-button")} 
    >
      {!isVisible ? <Menu size={22} className="" /> :""}
    </button>
  );
};
//  <X size={22} className="text-button-text" />