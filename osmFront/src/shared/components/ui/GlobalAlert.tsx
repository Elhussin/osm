import { useEffect, useState } from "react";
import { safeToast } from "@/src/shared/utils/safeToast";
import { GlobalAlertProps, GlobalAlertType } from "@/src/shared/types";

export default function GlobalAlert({
  message: propMessage,
  type: propType = "info",
}: GlobalAlertProps) {
  const [message, setMessage] = useState<string | null>(null);
  const [type, setType] = useState<GlobalAlertType>("info");
  const [show, setShow] = useState(false);

  useEffect(() => {
    const getCookie = (name: string): string | null => {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop()!.split(";").shift() || null;
      return null;
    };

    if (propMessage) {
      setMessage(propMessage);
      setType(propType);
      setShow(true);
    } else {
      const cookieMessage = getCookie("alert_message");
      const cookieType = getCookie("alert_type") as GlobalAlertType;

      if (cookieMessage) {
        setMessage(decodeURIComponent(cookieMessage));
        setType(cookieType || "info");
        setShow(true);

        // حذف الكوكي بعد العرض
        document.cookie =
          "alert_message=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
        document.cookie =
          "alert_type=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
      }
    }

    const timer = setTimeout(() => setShow(false), 5000);
    return () => clearTimeout(timer);
  }, [propMessage, propType]);

  // Trigger the toast as a side effect when we have a message to show
  useEffect(() => {
    if (show && message) {
      safeToast(message, { type });
    }
  }, [show, message, type]);

  // This component renders nothing; it only triggers a toast side-effect
  return null;
}
