
"use client";

// import { useFilteredListRequest } from "@/src/shared/hooks/useFilteredListRequest";
// import { useProductFormStore } from "../store/useProductFormStore";
// import { useEffect } from "react";

// export function useProductRelations() {
//   const fetchAttributes = useFilteredListRequest({ alias: "products_attribute_values_list", defaultPage: 1, defaultAll: true, defaultPageSize: 1000 });
//   const fetchSuppliers = useFilteredListRequest({ alias: "products_suppliers_list", defaultPage: 1, defaultAll: true, defaultPageSize: 1000 });
//   const fetchManufacturers = useFilteredListRequest({ alias: "products_manufacturers_list", defaultPage: 1, defaultAll: true, defaultPageSize: 1000 });
//   const fetchBrands = useFilteredListRequest({ alias: "products_brands_list", defaultPage: 1, defaultAll: true, defaultPageSize: 1000 });
//   const fetchCategories = useFilteredListRequest({ alias: "products_categories_list", defaultPage: 1, defaultAll: true, defaultPageSize: 1000 });

//   const { setData } = useProductFormStore();

//   const isLoading =
//     fetchAttributes.isLoading ||
//     fetchSuppliers.isLoading ||
//     fetchManufacturers.isLoading ||
//     fetchBrands.isLoading ||
//     fetchCategories.isLoading;

//   useEffect(() => {
//     // ✅ نتحقق أن البيانات وصلت فعلًا قبل التحديث
//     if (!isLoading) {
//       if (fetchAttributes.data?.length) setData("attribute-values", fetchAttributes.data);
//       if (fetchSuppliers.data?.length) setData("suppliers", fetchSuppliers.data);
//       if (fetchManufacturers.data?.length) setData("manufacturers", fetchManufacturers.data);
//       if (fetchBrands.data?.length) setData("brands", fetchBrands.data);
//       if (fetchCategories.data?.length) setData("categories", fetchCategories.data);
//     }
//   }, [
//     isLoading,
//     fetchAttributes.data,
//     fetchSuppliers.data,
//     fetchManufacturers.data,
//     fetchBrands.data,
//     fetchCategories.data,
//     setData,
//   ]);

//   // const data = {
//   //   attributes: fetchAttributes.data || [],
//   //   suppliers: fetchSuppliers.data || [],
//   //   manufacturers: fetchManufacturers.data || [],
//   //   brands: fetchBrands.data || [],
//   //   categories: fetchCategories.data || [],
//   // };

//   return {isLoading };
// }

"use client";

import { useFilteredListRequest } from "@/src/shared/hooks/useFilteredListRequest";
import { useProductFormStore } from "../store/useProductFormStore";
import { useEffect } from "react";

export function useProductRelations() {
  const fetchAttributes = useFilteredListRequest({ alias: "products_attribute_values_list", defaultPage: 1, defaultAll: true, defaultPageSize: 1000 });
  const fetchSuppliers = useFilteredListRequest({ alias: "products_suppliers_list", defaultPage: 1, defaultAll: true, defaultPageSize: 1000 });
  const fetchManufacturers = useFilteredListRequest({ alias: "products_manufacturers_list", defaultPage: 1, defaultAll: true, defaultPageSize: 1000 });
  const fetchBrands = useFilteredListRequest({ alias: "products_brands_list", defaultPage: 1, defaultAll: true, defaultPageSize: 1000 });
  const fetchCategories = useFilteredListRequest({ alias: "products_categories_list", defaultPage: 1, defaultAll: true, defaultPageSize: 1000 });

  const { setData } = useProductFormStore();


  useEffect(() => {
    if (fetchAttributes.data?.length) setData("attribute-values", fetchAttributes.data.reverse());
  }, [fetchAttributes.data]);
  
  useEffect(() => {
    if (fetchSuppliers.data?.length) setData("suppliers", fetchSuppliers.data.reverse());
  }, [fetchSuppliers.data]);
  
  useEffect(() => {
    if (fetchManufacturers.data?.length) setData("manufacturers", fetchManufacturers.data.reverse());
  }, [fetchManufacturers.data]);
  
  useEffect(() => {
    if (fetchBrands.data?.length) setData("brands", fetchBrands.data.reverse());
  }, [fetchBrands.data]);
  
  useEffect(() => {
    if (fetchCategories.data?.length) setData("categories", fetchCategories.data.reverse());
  }, [fetchCategories.data]);

  
  const isLoading =
    fetchAttributes.isLoading ||
    fetchSuppliers.isLoading ||
    fetchManufacturers.isLoading ||
    fetchBrands.isLoading ||
    fetchCategories.isLoading;

  return { isLoading };
}
