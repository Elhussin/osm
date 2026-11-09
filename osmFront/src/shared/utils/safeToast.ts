
import { toast } from "sonner";

const shownToasts = new Set<string>();
const timeouts = new Map<string, NodeJS.Timeout>();

export function safeToast(
  message: string,
  options?: {
    id?: string;
    description?: string;
    duration?: number;
    type?: "success" | "error" | "warning" | "info";
  }
) {
  const id = options?.id || message || `${Date.now()}-${Math.random()}`;

  if (shownToasts.has(id)) return;
  shownToasts.add(id);

  const duration = options?.duration ?? 5000; 
  clearToasts();
  toast(message, {
    id,
    description: options?.description,
    duration,
    ...options, 
  });

  const timeout = setTimeout(() => {
    shownToasts.delete(id);
    timeouts.delete(id);
  }, duration);

  timeouts.set(id, timeout);
}

export function clearToasts() {
  shownToasts.clear();

  for (const timeout of timeouts.values()) {
    clearTimeout(timeout);
  }
  timeouts.clear();

  toast.dismiss();
}
