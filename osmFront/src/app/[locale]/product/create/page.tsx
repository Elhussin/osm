"use client";
import React, { Suspense } from "react";
import { LoadingSpinner } from "@/src/shared/components/ui/loding";
const ProductVariantForm = React.lazy(
  () => import("@/src/features/products/components/ProductForm")
);

export default function CreatePrescriptionPage() {
  return (
    <Suspense
      fallback={
        <div>
          <LoadingSpinner />
        </div>
      }
    >
      <ProductVariantForm
        alias="products_product-variants_create"
        // title="create Product Variant"
        // message="Sucussfully created Product Variant"
        // submitText="Save Product Variant"
        // className="container"
      />
    </Suspense>
  );
}
