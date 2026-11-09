import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export const cn = (...args: Parameters<typeof clsx>) => clsx(...args);



export function cnFun(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
