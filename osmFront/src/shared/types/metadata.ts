export  interface MetadataOptions {
    title: string;
    description: string;
    keywords?: string[];
    canonicalUrl?: string;
    suffix?: string;
    openGraphImage?: string; // og image preview in social media
    openGraphType?: string; // og type of the content in OG (e.g: article)
    twitterCardType?: 'summary' | 'summary_large_image'; // twitter card type
    icons?: any;
  }
  
