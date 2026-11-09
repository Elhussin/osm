type Option = { label: string; value: string };

export const languages: Option[] = [
  { label: 'EN', value: 'en' },
  { label: 'AR', value: 'ar' },
];

export const countries: Option[] = [
  { label: 'KSA', value: 'sa' },
  { label: 'EGY', value: 'eg' },
  { label: 'UAE', value: 'ae' },
];

export const currencies: Option[] = [
  { label: 'SAR', value: 'sar' },
  { label: 'EGP', value: 'egp' },
  { label: 'AED', value: 'aed' },
];

// خريطة العملة حسب الدولة
export const currencyMap: Record<string, string> = {
  sa: 'sar',
  eg: 'egp',
  ae: 'aed',
};



export const IteamInPage= 5