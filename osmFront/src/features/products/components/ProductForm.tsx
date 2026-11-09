
"use client";
import { useEffect, useMemo } from "react";
import { Form } from "@/src/shared/components/shadcn/ui/form";
import { Button } from "@/src/shared/components/shadcn/ui/button";
import { Input } from "@/src/shared/components/shadcn/ui/input";
import { useApiForm } from "@/src/shared/hooks/useApiForm";
import { useProductFormStore } from "@/src/features/products/store/useProductFormStore";
import { useProductRelations } from "@/src/features/products/hooks/useProductRelations";
import {VariantRender} from "./VariantRender";

import {
  ProductConfig,
  MainFieldConfig,
  veriantConfig,
  CustomVariantConfig,
  CustomVariantMainConfig,
} from "@/src/features/products/constants/config";
import { handleSave } from "../utils/handleSave";
import { RenderFields } from "@/src/shared/components/field/RenderFields";
import { Loading } from "@/src/shared/components/ui/loding";
import { Dialog } from "./Dialog";

// ✅ المكون الرئيسي
export const ProductForm = ({ alias, id }: { alias: string; id?: string }) => {
  const defaultValues = {
    name: "",
    type: "",
    variant_type: "",
    variant_count: 0,
    is_active: true,
  };

  const form = useApiForm({
    alias: alias || "products_products_create",
    defaultValues,
  });

  const store = useProductFormStore();
  const { isLoading } = useProductRelations();

  const [productType, brand, model, variant_count, variant_type] = form.watch([
    "type",
    "brand",
    "model",
    "variant_count",
    "variant_type",
  ]);

  const isMainComplete =useMemo(
    () => [productType, variant_type].every((v) => v !== null && v !== undefined && v !== "" && v!==0),
    [productType, variant_type]
  );
  const isComplete = useMemo(
    () => [productType, brand, model].every((v) => v !== null && v !== undefined && v !== "" ),
    [productType, brand, model]
  );

  // ✅ فلترة الحقول حسب نوع المنتج مع useMemo لتجنب إعادة التنفيذ
  const filteredConfig = useMemo(() => {
    return ProductConfig.filter((item) => item.role === "all" || item.role === productType);
  }, [productType]);

  const submitText = id ? "Update" : "Save";

  // ✅ تجنب الحلقة اللا نهائية
  useEffect(() => {
    const newCount = Number(variant_count) || 0;
    if (store.variantCount !== newCount) {
      store.setVariantCount(newCount);
    }
  }, [variant_count]);

  if (isLoading) return <Loading />;

  return (
    <>
      <Form {...form}>
        <form
          onSubmit={(e) => e.preventDefault()}
          className="space-y-6 p-4 border rounded-lg max-w-xxl mx-auto"
        >
          <div className="grid grid-cols-1 md:grid-cols-1 gap-4">
            <RenderFields fields={MainFieldConfig.filter(f => f.name === "type")} form={form} />

            {productType && (
            <>
            <RenderFields fields={MainFieldConfig.filter(f => f.name === "variant_type")} form={form}  selectedType={productType} />

             {isMainComplete && (<RenderFields key={`${productType}`}  fields={filteredConfig}form={form} selectedType={productType}/>)}
            </>
          )}
          </div>
    {isComplete && (
        <>
        <VariantRender key={`${productType}-${variant_type}`}
         variant_type={variant_type} form={form} productType={productType} /> 

        <Button
          type="button"
          onClick={() => handleSave(form, store.variants, veriantConfig(variant_type))}
          disabled={form.isBusy}
          className={`bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md font-medium transition-colors ${
            form.isBusy ? "opacity-50 cursor-not-allowed" : ""
          }`}
        >
          {form.isBusy ? "Saving..." : submitText}
        </Button>
        </>
    )}
        </form>
      </Form>
      <Dialog setValue={form.setValue} />
    </>
  );
};

export default ProductForm;