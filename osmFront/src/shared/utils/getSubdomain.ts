

export const getSubdomain = (hostFromServer?: string): string | null => {
    const hostname =
      typeof window !== "undefined"
        ? window.location.hostname
        : hostFromServer?.split(":")[0] || "localhost";
  
    // 🟡 استثناء localhost
    if (hostname === "localhost") return null;
  
    // 🟠 دعم subdomain.localhost
    if (hostname.endsWith(".localhost")) {
      const parts = hostname.split(".");
      if (parts.length === 2) {
        return parts[0]; // مثلاً: sub.localhost → sub
      }
      return null;
    }
  
    // 🟢 حالات production (store1.example.com)
    const parts = hostname.split(".");
    if (parts.length > 2) {
      return parts[0]; // أول جزء هو الـ subdomain
    }
  
    return null;
  };
  


