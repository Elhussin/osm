import { notFound } from 'next/navigation';
export async function getTrenMessagesFiles(locale: string) {
    try {
      const common = (await import(`@/src/messages/${locale}/common.json`)).default;
      const formGenerator = (await import(`@/src/messages/${locale}/formGenerator.json`)).default;  
      const products = (await import(`@/src/messages/${locale}/products.json`)).default;  
      return { ...common, ...formGenerator, ...products };
    } catch (error) {
      notFound();
    }
  }