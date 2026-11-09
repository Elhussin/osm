// SearchButtonContext.tsx
"use client";
import { createContext, useContext, useState, ReactNode, useCallback } from "react";

interface SearchButtonContextType {
  isVisible: boolean;
  toggle: () => void;
  show: () => void;
  hide: () => void;
}

const SearchButtonContext = createContext<SearchButtonContextType | undefined>(undefined);

export const SearchButtonProvider = ({ children }: { children: ReactNode }) => {
  const [isVisible, setIsVisible] = useState(false);

  // استخدم useCallback حتى لا تتغير الدوال في كل render
  const toggle = useCallback(() => setIsVisible((prev) => !prev), []);
  const show = useCallback(() => setIsVisible(true), []);
  const hide = useCallback(() => setIsVisible(false), []);

  return (
    <SearchButtonContext.Provider value={{ isVisible, toggle, show, hide }}>
      {children}
    </SearchButtonContext.Provider>
  );
};

export const useSearchButton = () => {
  const context = useContext(SearchButtonContext);
  if (!context) {
    throw new Error("useSearchButton must be used within a <SearchButtonProvider>");
  }
  return context;
};
