// useProductFormStore.ts
import { create } from "zustand";

interface ProductFormState {
  variantCount: number;
  variants: Record<string, any>[];
  openVariantIndex: number | null;
  isSubmitting: boolean;
  isShowModal: boolean;
  entityName: string;
  currentFieldName: string;
  isVariant: boolean;
  setVariantCount: (count: number) => void;
  setVariantField: (index: number, field: string, value: any) => void;
  toggleVariant: (index: number) => void;
  setIsSubmitting: (value: boolean) => void;
  setShowModal: (value: boolean) => void;
  setEntityName: (name: string) => void;
  setCurrentFieldName: (name: string) => void;
  setIsVariant: (value: boolean) => void;
  setOpenVariantIndex: (index: number | null) => void;
  data: Record<string, any[]>; // كل entity عبارة عن array
  setData: (entity: string, newItem: any) => void;
  attributeCount: number;
  setAttributeCount: (count: number) => void;
  isAttribute: boolean;
  setIsAttribute: (value: boolean) => void;
}
  
export const useProductFormStore = create<ProductFormState>((set, get) => ({
  variantCount: 1,
  variants: [{}],
  openVariantIndex: null,
  isSubmitting: false,
  isShowModal: false,
  entityName: "",
  currentFieldName: "",
  isVariant: false,
  attributeCount: 0,
  isAttribute: false,

  // setVariantCount: (count: number) =>
  //   set((state) => {
  //     const updated = [...state.variants];
  //     if (count > state.variants.length) {
  //       updated.push(...Array.from({ length: count - state.variants.length }, () => ({})));
  //     } else if (count < state.variants.length) {
  //       updated.length = count;
  //     }
  //     // if openVariantIndex is now out of range, close it
  //     const openIdx = get().openVariantIndex;
  //     const newOpenIdx = openIdx !== null && openIdx >= count ? null : openIdx;
  //     return { variantCount: count, variants: updated, openVariantIndex: newOpenIdx };
  //   }),
  setVariantCount: (count: number) =>
  set((state) => {
    if (state.variantCount === count) return state; // ✅ لا تحدث أي تغييرات

    const updated = [...state.variants];
    if (count > state.variants.length) {
      updated.push(...Array.from({ length: count - state.variants.length }, () => ({})));
    } else if (count < state.variants.length) {
      updated.length = count;
    }

    const openIdx = get().openVariantIndex;
    const newOpenIdx = openIdx !== null && openIdx >= count ? null : openIdx;

    return { variantCount: count, variants: updated, openVariantIndex: newOpenIdx };
  }),


  setVariantField: (index: number, field: string, value: any) =>
    set((state) => {
      if (typeof index !== "number" || index < 0) return { variants: state.variants };
      const updated = [...state.variants];
      updated[index] = { ...updated[index], [field]: value };
      return { variants: updated };
    }),

  toggleVariant: (index: number) =>
    set((state) => ({
      openVariantIndex: state.openVariantIndex === index ? null : index,
    })),

  setIsSubmitting: (value: boolean) => set({ isSubmitting: value }),
  setShowModal: (value: boolean) => set({ isShowModal: value }),
  setEntityName: (name: string) => set({ entityName: name }),
  setCurrentFieldName: (name: string) => set({ currentFieldName: name }),
  setIsVariant: (value: boolean) => set({ isVariant: value }),
  setOpenVariantIndex: (index: number | null) => set({ openVariantIndex: index }),
  setAttributeCount: (count: number) => set({ attributeCount: count }),
  setIsAttribute: (value: boolean) => set({ isAttribute: value }),

  data: {
    "attribute-values": [],
    suppliers: [],
    manufacturers: [],
    brands: [],
    categories: [],
  },


    // setData: (key, value) =>
    //   set((state) => {
    //     const existing = state.data[key];
    //     // نتأكد أن البيانات مختلفة فعلًا قبل إعادة تعيينها
    //     if (JSON.stringify(existing) === JSON.stringify(value)) return state;
    //     return { data: { ...state.data, [key]: value } };
    //   }),
    setData: (key, value) =>
      set((state) => {
        const existing = state.data[key] || [];
    
        // ✅ إذا القيمة مصفوفة، نستبدلها بالكامل
        if (Array.isArray(value)) {
          if (JSON.stringify(existing) === JSON.stringify(value)) return state;
          return { data: { ...state.data, [key]: value } };
        }
    
        // ✅ إذا القيمة عنصر واحد، نضيفه فقط إذا لم يكن موجودًا
        const exists = existing.some((item: any) => item.id === value.id);
        const updated = exists ? existing : [...existing, value];
    
        return { data: { ...state.data, [key]: updated } };
      }),
    
    
}));
