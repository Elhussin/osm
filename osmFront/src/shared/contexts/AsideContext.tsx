'use client';
import React, { createContext, useState, useContext, ReactNode } from 'react';
import MainLayout from '@/src/shared/components/layout/MainLayout';

type AsideContextType = {
  asideContent: ReactNode | null;
  isVisible: boolean;

  toggleAside: () => void;
  setAsideContent: (content: ReactNode | null) => void;
};

const AsideContext = createContext<AsideContextType | undefined>(undefined);

export function AsideProvider({ children }: { children: ReactNode }) {
  const [asideContent, setAsideContent] = useState<ReactNode>(null);
  const [isVisible, setIsVisible] = useState(false);

  const toggleAside = () => setIsVisible((prev) => !prev);


  return (
    <AsideContext.Provider
      value={{ asideContent, isVisible, toggleAside, setAsideContent }}
    >
      <MainLayout
        mainContent={children}
        // asideContent={ isVisible ? asideContent || <Aside /> : null}
      />
    </AsideContext.Provider>
  );
}

export function useAside() {
  const context = useContext(AsideContext);
  if (!context) {
    throw new Error('useAside must be used within an AsideProvider');
  }
  return context;
}
