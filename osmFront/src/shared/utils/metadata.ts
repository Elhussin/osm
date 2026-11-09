// import { MetadataOptions } from "@/types/metadata";
//   export function generateMetadata({
//     title,
//     description,
//     keywords = [],
//     canonicalUrl,
//     suffix = 'Solo Vizion',
//     openGraphImage,
//     openGraphType = 'website',
//     twitterCardType = 'summary_large_image',
//   }: MetadataOptions) {
//     const fullTitle = `${title} | ${suffix}`;
  
//     return {
//       title: fullTitle,
//       description,
//       keywords,
//       alternates: canonicalUrl
//         ? {
//             canonical: canonicalUrl,
//           }
//         : undefined,
//       openGraph: {
//         title: fullTitle,
//         description,
//         type: openGraphType,
//         url: canonicalUrl,
//         images: openGraphImage ? [{ url: openGraphImage }] : undefined,
//       },
//       twitter: {
//         card: twitterCardType,
//         title: fullTitle,
//         description,
//         images: openGraphImage ? [openGraphImage] : undefined,
//       },
//     };
//   }
  


import { MetadataOptions } from "@/src/shared/types/metadata";
// import type { MetadataIcon } from 'next/dist/lib/metadata/types/metadata-types'; // Import this if needed for type safety

export function generateMetadata({
  title,
  description,
  keywords = [],
  canonicalUrl,
  suffix = 'Solo Vizion',
  openGraphImage,
  openGraphType = 'website',
  twitterCardType = 'summary_large_image',
  icons, // <--- Add this line
}: MetadataOptions) {
  const fullTitle = `${title} | ${suffix}`;

  return {
    title: fullTitle,
    description,
    keywords,
    alternates: canonicalUrl
      ? {
          canonical: canonicalUrl,
        }
      : undefined,
    openGraph: {
      title: fullTitle,
      description,
      type: openGraphType,
      url: canonicalUrl,
      images: openGraphImage ? [{ url: openGraphImage }] : undefined,
    },
    twitter: {
      card: twitterCardType,
      title: fullTitle,
      description,
      images: openGraphImage ? [openGraphImage] : undefined,
    },
    icons, 
  };
}