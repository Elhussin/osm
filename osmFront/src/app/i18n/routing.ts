
import {defineRouting} from 'next-intl/routing';
const locales = process.env.NEXT_PUBLIC_LOCALES?.split(',') ?? ['en'];

export const routing = defineRouting({
  locales,
  defaultLocale: process.env.DEFAULT_LANGUAGE as "en" | "ar",

});