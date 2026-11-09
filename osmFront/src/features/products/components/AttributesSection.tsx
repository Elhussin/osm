import { useFieldArray, useFormContext } from "react-hook-form";
import { Button } from "@/src/shared/components/shadcn/ui/button";
import { RenderFields } from "../../../shared/components/field/RenderFields";
import { CustomVariantConfig } from "@/src/features/products/constants/config";

export const AttributesSection = ({ variantIndex ,form}: { variantIndex: number ,form:any}) => {
  // const { control } = useFormContext();

  // إدارة الـ attributes الخاصة بكل variant
  const { fields: attributes, append: addAttr } = useFieldArray({
    control:form.control,
    name: `variants.${variantIndex}.attributes`,
  });

  return (
    <div className="space-y-3">
      {attributes.map((attr, attrIndex) => (
        <div key={attr.id || attrIndex} className="border p-2 rounded">
          <p className="font-semibold text-sm mb-1">
            Attribute {attrIndex + 1}
          </p>

          <RenderFields
            fields={CustomVariantConfig}
            form={form}
            variantNumber={variantIndex}
            attributeIndex={attrIndex}
          />
        </div>
      ))}

      <Button
        type="button"
        onClick={() => addAttr({ key: "", value: "" })}
        className="mt-2"
        variant="outline"
      >
        + Add Attribute
      </Button>
    </div>
  );
};
