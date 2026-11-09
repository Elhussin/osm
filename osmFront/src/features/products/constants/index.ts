import { ProductForginKeyConfigType } from "@/src/features/products/types";

export const TypeEnum = [{ value: "CL", label: "Contact Lens" }, { value: "SL", label: "Spectacle Lens" }, { value: "FR", label: "Frames" }, { value: "AX", label: "Accessories" }, { value: "DV", label: "Devices" }, { value: "OT", label: "Other" }]
export const VariantTypeEnum = [{ value: "CL", label: "Contact Lens" }, { value: "SL", label: "Spectacle Lens" }, { value: "FR", label: "Frames" }, { value: "AX", label: "Accessories" }, { value: "DV", label: "Devices" }, { value: "OT", label: "Other" }]
export const ProductTypeEnum=[
  {value:"SV-ST",label:"Single Stock", filter:"SL",
  },
  {
    value:"SV-RX",
    label:"Single RX",
    filter:"SL",
  },
  {
    value:"MF-RX",
    label:"Multi Focal ",
    filter:"SL",
  },
  {
    value:"BF-RX",
    label:"Bifocal RX",
    filter:"SL",
  },

  {
    value:"CL-Cl",
    label:"Contact Lens Clear",
    filter:"CL",
  },
  {
    value:"CL-CO",
    label:"Contact Lens Colored",
    filter:"CL",
  },
  {
    value:"FR-SG",
    label:"Frames Sun Glasses",
    filter:"FR",
  },
  {
    value:"FR-SP",
    label:"Frames Spectacle Glasses",
    filter:"FR",
  }
]




export const ProductConfig: Record<string, ProductForginKeyConfigType> = {
// export const ProductConfig: ProductForginKeyConfigType[] = [

 "model":{
    name: "model",
    label: "Model",
    type: "text",
    role: "all",
    filter: "Model",
    title: "Enter Product Model | Model Number",
    entityName: "",
    fieldName: "",
    placeholder: "Model...",
    required: true,
  },
 "name": {
    name: "name",
    label: "Name",
    role: "all",
    filter: "Name",
    title: "Enter Product Name",
    entityName: "",
    fieldName: "",
    type: "text",
    placeholder: "Name...",
    required: false,
  },
  "category":{
    name: "category_id",
    label: "Category",
    role: "all",
    filter: "categories",
    title: "Select Main Category",
    subFilter: "",
    entityName: "categories",
    fieldName: "name",
    type: "foreignkey",
    placeholder: "Select Category...",
    required: true,
    mapOnly: true,

  },
  "supplier":{
    name: "supplier_id",
    label: "Supplier",
    role: "all",
    filter: "suppliers",
    title: "Select Supplier | Supplier Name",
    entityName: "suppliers",
    fieldName: "name",
    type: "foreignkey",
    placeholder: "Select Supplier...",
    required: true,
    mapOnly: true, // use to map only the data without any other data
  },
  "manufacturer":{
    name: "manufacturer_id",
    label: "Manufacturer",
    role: "all",
    filter: "manufacturers",
    title: "Select Manufacturer | Manufacturer Name",
    entityName: "manufacturers",
    fieldName: "name",
    type: "foreignkey",
    required: true,
    mapOnly: true,
  },
  "brand":{
    name: "brand_id",
    label: "Brand",
    role: "all",
    filter: "brands",
    title: "Select Brand | Brand Name",
    entityName: "brands",
    fieldName: "name",
    type: "foreignkey",
    required: true,
    mapOnly: true,
  },
  "type": {
    name: "type",
    label: "Type",
    role: "all",
    filter: "Type",
    title: "Select Product Type",
    entityName: "products",
    fieldName: "type",
    type: "select",
    placeholder: "Select Product Type...",
    required: true,
    options: TypeEnum,
  },
  "variant_type":{
    name: "variant_type",
    label: "Variant Type",
    role: "all",
    filter: "Variant Type",
    title: "Select Variant Type",
    entityName: "products",
    fieldName: "variant_type",
    type: "select",
    placeholder: "Select Variant Type...",
    required: true,
    options: VariantTypeEnum,
  },
  "is_active":{
    name: "is_active",
    label: "Is Active",
    role: "all",
    filter: "Is Active",
    subFilter: "",
    title: "Is Active | True | False",
    entityName: "",
    fieldName: "is_active",
    type: "checkbox",
    placeholder: "Select Is Active...",
    required: false,
    
  },
}

export const MainTypeConfig : ProductForginKeyConfigType[] = [
  {
    name: "type",
    label: "Type",
    role: "all",
    filter: "Type",
    title: "Select Product Type",
    entityName: "products",
    fieldName: "type",
    type: "select",
    placeholder: "Select Product Type...",
    required: true,
    options: TypeEnum,
  },
  {
    name: "product_type_id",
    label: "Product Type",
    role: "all",
    filter: "Product Type",
    subFilter: "",
    title: "Product Type Sun Glasses ,Color Contact lens",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    placeholder: "Select product type...",
    required: true,
    options: ProductTypeEnum,
  },
]