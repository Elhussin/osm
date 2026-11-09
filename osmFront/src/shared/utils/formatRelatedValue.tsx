
import Image from "next/image";
import { 
  isValidDate, 
  formatDate, 
  isImageUrl, 
  handleDownloadPDF, 
  handleCopy, 
  handlePrint 
} from "@/src/shared/utils/cardViewHelper";

export function formatRelatedValue(value: any, key: string, t: (key: string) => string): React.ReactNode {
    if (value == null) return "N/A";
  
    if (typeof value === "boolean") {
      // return value ? "✅" : "❌";
      try {
        return `${t(`values.${key}.${value}`)} ${value ? "✅" : "❌"}`;
      } catch {
        return value ? "✅" : "❌";
      }
    }
  
    // string
    if (typeof value === "string") {
      if (isImageUrl(value)) {
        return (
          <Image
            src={value}
            alt="image"
            width={120}
            height={120}
            className="rounded-md border"
          />
        );
      }
      if (isValidDate(value)) {
        return formatDate(value);
      }
      return value;
    }
  
    // number
    if (typeof value === "number") return value;
  
    // array
    if (Array.isArray(value)) {
      return value.map((v, i) => (
        <span key={i} className="mr-1">
          {formatRelatedValue(v, key, t)}
          {i < value.length - 1 && ", "}
        </span>
      ));
    }
  
    // object
    if (typeof value === "object") {
      const preferredKeys = ["name", "title", "label", "username", "email"];
      for (const key of preferredKeys) {
        if (key in value && value[key]) return String(value[key]);
      }
  
      // fallback: أول نص
      const firstValue = Object.values(value).find((v) => typeof v === "string");
      if (firstValue) return String(firstValue);
  
      return JSON.stringify(value);
    }
  
    return String(value);
  }
  
  export function formatTranslatedValue(
    key: string,
    value: any,
    t: (key: string) => string
  ): React.ReactNode {
    if (value == null) return "N/A";
  
    if (typeof value === "boolean") {
      try {
        return t(`values.${key}.${value}`);
      } catch {
        return value ? "✅" : "❌";
      }
    }
  
    if (typeof value === "string") {
      try {
        return t(`values.${key}.${value}`);
      } catch {
        return value;
      }
    }
  
    if (Array.isArray(value)) {
      return value.map((v, i) => (
        <span key={i} className="mr-1">
          {formatTranslatedValue(key, v, t)}
          {i < value.length - 1 && ", "}
        </span>
      ));
    }
  
    return JSON.stringify(value);
  }
  