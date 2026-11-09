import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { useSearchButton } from "@/src/shared/contexts/SearchButtonContext";

export function AutoHideSearchOnRouteChange() {
  const pathname = usePathname();
  const { hide } = useSearchButton();

  useEffect(() => {
    hide(); // يخفي الزر كلما تغيّر المسار
  }, [pathname]);

  return null;
}
