import { useFieldArray, useFormContext } from "react-hook-form";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/src/shared/components/shadcn/ui/accordion";
import { Button } from "@/src/shared/components/shadcn/ui/button";
import { RenderFields } from "@/src/shared/components/field/RenderFields";
import { useProductFormStore } from "@/src/features/products/store/useProductFormStore";
import { veriantConfig } from "@/src/features/products/constants/config";
import { CustomVariantMainConfig } from "@/src/features/products/constants/config";
import { AttributesSection } from "./AttributesSection";

export const VariantRender = ({ variant_type, productType,form }: any) => {
  const store = useProductFormStore();


  // قائمة الـ variants
  const { fields: variants, append: addVariant } = useFieldArray({
    control:form.control,
    name: "variants",
  });

  return (
    <Accordion
      type="single"
      collapsible
      className="w-full"
      value={store.openVariantIndex !== null ? String(store.openVariantIndex) : undefined}
      onValueChange={(val) => {
        const idx = val ? Number(val) : null;
        store.setOpenVariantIndex(idx);
      }}
    >
      {variants.map((variant, variantIndex) => (
        <AccordionItem key={variant.id || variantIndex} value={String(variantIndex)}>
          <AccordionTrigger className="font-bold border-b p-2">
            Variant {variantIndex + 1}
          </AccordionTrigger>

          <AccordionContent className="p-4 space-y-4">
            {/* --- حقول الـ variant الأساسية --- */}
            <RenderFields
             form={form}
             fields={variant_type === "custom" ? CustomVariantMainConfig : veriantConfig(variant_type)}
              variantNumber={variantIndex}
              selectedType={productType}
            />

            {/* --- الحقول الخاصة بالـ attributes داخل هذا الـ variant --- */}
            <AttributesSection variantIndex={variantIndex} form={form}/>
          </AccordionContent>
        </AccordionItem>
      ))}

      <Button
        type="button"
        onClick={() => addVariant({ name: "", sku: "", attributes: [] })}
        className="mt-2"
      >
        + Add Variant
      </Button>
    </Accordion>
  );
};
