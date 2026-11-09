"use client";
import Header from "./Header";
import Footer from "./Footer";
import { Toaster } from "sonner";
import GlobalAlert from "../ui/GlobalAlert";
import { usePathname } from "next/navigation";
import Aside from "./Aside";
import { useAside } from "@/src/shared/contexts/AsideContext";
import clsx from "clsx";
import { useLocale } from "next-intl";
interface Props {
  mainContent?: React.ReactNode;
}

export default function MainLayout({ mainContent }: Props) {
  const pathname = usePathname();
  const excluded = ["/auth/login", "/auth/register"];

  const showAside = !excluded.includes(pathname);
  const { isVisible } = useAside();

  const locale = useLocale();
  const isRTL = locale === "ar";
  return (
    <div className="flex flex-col min-h-screen pt-16 ">
      <div className="fixed top-0 left-0 w-full z-30 shadow-sm">
        <Header />
      </div>

      <div className={clsx("flex flex-1 min-h-0")}>
        {showAside && <Aside />}

        <main className="flex-1 min-w-0">
          <div className="container mx-auto p-4 sm:p-6 lg:p-8 animate-in fade-in duration-500">
            <GlobalAlert />
            {mainContent}
            {/* <Toaster /> */}
            <Toaster
              richColors
              closeButton
              position="top-right"
              duration={4000}
              toastOptions={{
                classNames: {
                  success: "bg-green-600 text-white",
                  error: "bg-red-600 text-white",
                  warning: "bg-yellow-500 text-black",
                  info: "bg-blue-500 text-white",
                },
              }}
            />
          </div>
        </main>
      </div>
      <Footer />
    </div>
  );
}
