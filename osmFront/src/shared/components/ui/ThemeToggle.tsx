

"use client"
import { useEffect, useState, useRef } from "react";
import { Palette, Check } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export const themes: { id: string; label: string }[] = [
  { id: "theme-light", label: "Light" },
  { id: "dark", label: "Dark" },
  { id: "theme-ocean", label: "Ocean" },
  { id: "theme-green", label: "Green" },
  { id: "theme-warm", label: "Warm" },
  { id: "theme-forest", label: "Forest" },
  { id: "theme-olive", label: "Olive" },
];
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Theme toggle component
 * @description A modern, accessible dropdown to toggle the application theme.
 * usage: <ThemeToggle />
 * @returns {JSX.Element}
 */
export default function ThemeToggle() {
  const [theme, setTheme] = useState("theme-light");
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Initialize theme from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("theme");
    if (saved && themes.find((t) => t.id === saved)) {
      setTheme(saved);
      document.documentElement.className = saved;
    } else {
      document.documentElement.className = "theme-light";
    }
  }, []);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleThemeChange = (newThemeId: string) => {
    setTheme(newThemeId);
    document.documentElement.className = newThemeId;
    localStorage.setItem("theme", newThemeId);
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "p-2 rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary/50",
          isOpen ? "bg-primary/10 text-primary" : "text-main hover:bg-surface hover:text-primary"
        )}
        title={"Theme"}
        aria-label="Toggle theme"
        aria-expanded={isOpen}
      >
        <Palette className="w-5 h-5" />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="absolute right-0 mt-2 w-48 py-2 bg-elevated border border-border-main rounded-xl shadow-xl z-50 overflow-hidden"
          >
            <div className="px-3 py-2 text-xs font-semibold text-secondary uppercase tracking-wider mb-1 border-b border-border-main/50">
              {"Select Theme"}
            </div>
            <div className="max-h-[300px] overflow-y-auto scrollbar-hide">
              {themes.map((t) => (
                <button
                  title={t.label}
                  key={t.id}
                  onClick={() => handleThemeChange(t.id)}
                  className={cn(
                    "w-full px-4 py-2 text-sm text-left flex items-center justify-between transition-colors cursor-pointer",
                    theme === t.id
                      ? "bg-primary/10 text-main/90 font-medium"
                      : "text-main hover:bg-surface hover:text-primary"
                  )}
                >
                  <span className="flex items-center gap-2">
                    {/* Optional: Add a colored dot representing the theme colors if hardcoded logic existed, 
                            but for now just the label is fine. */}
                    {t.label}
                  </span>
                  {theme === t.id && <Check className="w-4 h-4" />}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
