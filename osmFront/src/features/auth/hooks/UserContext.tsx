"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
  useMemo,
} from "react";
import { safeToast } from "@/src/shared/utils/safeToast";
import { useRouter } from "@/src/app/i18n/navigation";
import { useTranslations } from "next-intl";
import { UserContextType, User } from "@/src/shared/types";
import { useApiForm } from "@/src/shared/hooks/useApiForm";
const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const t = useTranslations("userContext");

  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const fetchUser = useApiForm({ alias: "users_profile_retrieve" });
  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await fetchUser.query.refetch();
        if (res?.data) {
          setUser(res.data);
        } else {
          setUser(null);
        }
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const logoutRequest = useApiForm({
    alias: "users_logout_create",
    onSuccess: () => {
      setUser(null);
      router.replace(`/auth/login`);
      safeToast(t("logoutSuccess"), { type: "success" });
    },
  });

  const logout = async () => {
    try {
      await logoutRequest.submitForm();
    } catch {
      safeToast(t("logoutError"), { type: "error" });
    }
  };

  const value: UserContextType = useMemo(
    () => ({
      user,
      setUser,
      loading,
      refetchUser: async () => {
        try {
          const res = await fetchUser.query.refetch();
          if (res?.data) setUser(res.data);
          return res;
        } catch {
          setUser(null);
          return null;
        }
      },
      logout,
    }),
    [user, loading]
  );

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return context;
};
