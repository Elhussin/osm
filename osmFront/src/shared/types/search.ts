
  // ✅ types/search.ts
  export interface SearchField {
    name: string;
    label: string;
    type?: 'text' | 'select';
    options?: { label: string; value: string }[];
  }
  
  