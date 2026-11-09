// import ExampleForm from "@/src/shared/try";
// import DynamicFormWithFK from "@/src/shared/DynamicFormWithFK";

// export default function TryPage() {
//     return (
//         <DynamicFormWithFK />
//     );
// }
// "use client";
// import { z } from "zod";
// import { VariantTypeEnum as VariantTypeEnumType } from "@/src/features/products/constants";
// const VariantTypeEnum = z.enum([
//   "basic",
//   "frames",
//   "stockLenses",
//   "rxLenses",
//   "contactLenses",
//   "custom",
// ]);

// export const ProductRequest = z.object({
//   is_active: z.boolean().optional(),
//   is_deleted: z.boolean().optional(),
//   model: z.string().min(1).max(50),
//   name: z.string().max(200).nullish(),
//   variant_type: VariantTypeEnum.optional(),
//   category: z.number().int(),
//   supplier: z.number().int(),
//   manufacturer: z.number().int(),
//   brand: z.number().int(),
// });

// // Example config (DynamicForm)
// export const productFormFields = [
//   { name: "model", label: "Model", type: "text", required: true },
//   { name: "name", label: "Name", type: "text" },
//   { name: "variant_type", label: "Variant Type", type: "select", options: VariantTypeEnumType },
//   { name: "category", label: "Category", type: "select", optionsEndpoint: "categories" },
//   { name: "supplier", label: "Supplier", type: "select", optionsEndpoint: "suppliers" },
//   { name: "manufacturer", label: "Manufacturer", type: "select", optionsEndpoint: "manufacturers" },
//   { name: "brand", label: "Brand", type: "select", optionsEndpoint: "brands" },
//   { name: "is_active", label: "Active", type: "switch" },
//   { name: "is_deleted", label: "Deleted", type: "switch" },
// ];

// // import { ProductRequest, productFormFields } from "@/schemas/product";
// import DynamicFormWithFK from "@/src/features/products/components/DynamicFormWithFK";
import {ProductForm} from "@/src/features/products/components/ProductForm";
export default function ProductPage() {
  return (
    <div className="p-8">
      <ProductForm
        alias="products_products_create"
        // fields={productFormFields}
        // onSubmit={(data) => console.log("Submitted:", data)}
      />
    </div>
  );
}
