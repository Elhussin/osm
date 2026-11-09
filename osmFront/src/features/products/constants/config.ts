import { ProductConfigType } from "@/src/features/products/types";
import { generateLensOptions } from "@/src/features/products/utils/generateLensOptions";




export const PRODUCT_TYPE_CHOICES = [
    { value: "CL", label: "Contact Lens" },
    { value: "SL", label: "Spectacle Lens" },
    { value: "FR", label: "Frames" },
    { value: "AX", label: "Accessories" },
    { value: "DV", label: "Devices" },
    { value: "OT", label: "Other" }
]

export const VARIANT_TYPE_CHOICES = [
    { value: "basic", label: "Basic" , role:"all"},
    { value: "frames", label: "Frames" ,role:"FR"},
    { value: "stockLenses", label: "Stock Lenses" ,role:"SL"},
    { value: "rxLenses", label: "Rx Lenses" ,role:"SL"},
    { value: "contactLenses", label: "Contact Lenses" ,role:"CL"},
    { value: "custom", label: "Custom" ,role:"all"}
]

export const ProductConfig: ProductConfigType[] = [
    {
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
    {
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
    {
        name: "category",
        label: "Category",
        role: "all",
        filter: "categories",
        title: "Select Main Category",
        subFilter: "",
        entityName: "categories",
        fieldName: "name",
        type: "multiCheckbox",
        placeholder: "Select Category...",
        required: true,
        mapOnly: true,

    },
    {
        name: "brand",
        label: "Brand",
        role: "all",
        filter: "brands",
        subFilter: "product_type",
        title: "Select Brand | Brand Name",
        entityName: "brands",
        fieldName: "name",
        type: "foreignkey",
        required: true,
        mapOnly: true,
    },
    {
        name: "is_active",
        label: "Is Active",
        role: "all",
        filter: "Is Active",
        subFilter: "",
        title: "Is Active | True | False",
        entityName: "",
        fieldName: "is_active",
        type: "switch",
        placeholder: "Select Is Active...",
        required: false,

    },
]

export const MainFieldConfig : ProductConfigType[] = [
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
        options: PRODUCT_TYPE_CHOICES,
    },
    {
        name: "variant_count",
        label: "Variant Count",
        role: "all",
        filter: "Variant Count",
        title: "Select Variant Count",
        entityName: "products",
        fieldName: "variant_count",
        type: "number",
        placeholder: "Select Variant Count...",
        required: true,
        defaultValue: 1,
        className:"w-full",
        // onChange: (value: any) => {setVariantCount(Number(value))}
    },
        {
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
        options: VARIANT_TYPE_CHOICES,
    },
    {name:"attribute_count",label:"Attribute Count",type:"number",role:"all",filter:"",entityName:"",fieldName:"",required:true},

  ]

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



export const BasicVariantConfig: ProductConfigType[] = [

  {
    label: "SKU",
    name: "sku",
    role: "all",
    filter: "SKU",
    subFilter: "",
    title: "SKU is unique identifier for product | 123456789 |...",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "text",
    placeholder: "Enter SKU...",
    required: false,
  },
  {
    name: "product_type",
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
  {
    name: "warranty",
    label: "Warranty",
    role: "all",
    filter: "Warranty",
    subFilter: "",
    title: "Warranty | 1year | 2year | 3year |...",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    placeholder: "Select warranty...",
    required: false,
  },
  {
    name: "weight",
    label: "Weight",
    role: "all",
    filter: "Weight",
    subFilter: "",
    title: "Weight | 100g | 200g | 300g |...",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    placeholder: "Select weight...",
    required: false,
  },
  {
    name: "dimensions",
    label: "Dimensions",
    role: "all",
    filter: "Dimensions",
    subFilter: "",
    title: "Dimensions | 12mm | 13mm | 14mm |...",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    placeholder: "Select dimensions...",
    required: false,
  },
  {
    label: "Last Purchase Price",
    name: "last_purchase_price",
    role: "all",
    filter: "Last Purchase Price",
    subFilter: "",
    title: "Last Purchase Price | 100 | 200 | 300 |...",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "text",
    placeholder: "Enter last purchase price...",
    required: true,
  },
  {
    label: "Selling Price",
    name: "selling_price",
    role: "all",
    filter: "Selling Price",
    subFilter: "",
    title: "Selling Price | 100 | 200 | 300 |...",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "text",
    placeholder: "Enter selling price...",
    required: true,
  },
  {
    label: "Discount Percentage",
    name: "discount_percentage",
    role: "all",
    filter: "Discount Percentage",
    subFilter: "",
    title: "Discount Percentage | 10 | 20 | 30 |...",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "number",
    placeholder: "Enter discount percentage (%)",
    required: true,
  
  }
]

export const FrameVariantConfig: ProductConfigType[] = [
  {
    name: "frame_color_id",
    label: "Frame Color",
    role: "FR",
    filter: "Color",
    subFilter: "",
    title: "Frame Color | Black | White | Brown | Green |...",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    placeholder: "Select color...",
    required: true,
  },
  {
    name: "lens_diameter_id",
    label: "Lens Diameter",
    role: "all",
    filter: "Diameter",
    subFilter: "",
    title: "Lens Diameter | 12mm | 13mm | 14mm |...",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    placeholder: "Select diameter...",
    required: true,
  },
  {
    name: "temple_length_id",
    label: "Temple Length",
    role: "FR",
    filter: "Length",
    subFilter: "",
    title: "Frame Temple Length ",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    placeholder: "Select length...",
    required: true,
  },
  {
    name: "bridge_width_id",
    label: "Bridge Width",
    role: "FR",
    filter: "Width",
    subFilter: "",
    title: "Frame Bridge Width",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    placeholder: "Select width...",
    required: true,
  },
  {
    name: "frame_shape_id",
    label: "Frame Shape",
    role: "FR",
    filter: "Shape",
    subFilter: "",
    title: "Frame Shape | Circle | Oval | Square | Rectangle",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    placeholder: "Select shape...",
    required: true,
  },
  {
    name: "frame_material_id",
    label: "Frame Material",
    role: "FR",
    filter: "Material",
    subFilter: "",
    title: "Frame Material | Metal | Plastic | Wood | Glass",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    placeholder: "Select material...",
    required: true,
  },
  {
    name: "lens_color_id",
    label: "Lens Color",
    role: "all",
    filter: "Color",
    subFilter: "",
    title: "Lens Color | Brown | Green | Blue |...",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    placeholder: "Select lens color...",
    required: true,
  },
]


export const BaseLensVariantConfig: ProductConfigType[] = [
  {
    name: "lens_diameter",
    label: "Lens Diameter",
    role: "all",
    filter: "Diameter",
    subFilter: "",
    title: "Lens Diameter | 12mm | 13mm | 14mm |...",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    placeholder: "Select diameter...",
    required: true,
  },
  {
    name: "lens_color",
    label: "Lens Color",
    role: "all",
    filter: "Color",
    subFilter: "",
    title: "Lens Color | Brown | Green | Blue |...",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    placeholder: "Select lens color...",
    required: true,
  },
  {
    name: "lens_material",
    label: "Lens Material",
    role: "all",
    filter: "Material",
    subFilter: "",
    title: "Lens Material | Polycarbonate | CR-39 | Silicone |...",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    placeholder: "Select lens material...",
    required: true,
  },
  {
  name: "lens_coatings",
  label: "Lens Coatings",
  role: "all",
  filter: "Coatings",
  subFilter: "",
  title: "Lens Coatings | Anti-reflective | UV Protection | Scratch Resistant |...",
  entityName: "attribute-values",
  fieldName: "attribute_name",
  type: "multiCheckbox",
  placeholder: "Select coatings...",
  required: true,
},
{
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
]

// Base Lens | Stock Lenses 
export const StockLensVariantConfig: ProductConfigType[] = [
  {
    name: "spherical",
    label: "SPH",
    role: "SL",
    filter: "",
    subFilter: "SL-ST",
    title: "SPH | -60 | -50 | -40 |...",
    entityName: "products",
    fieldName: "spherical",
    type: "select",
    placeholder: "Select SPH...",
    required: true,
    options: generateLensOptions(-60, 60),
  },
  {
    name: "cylinder",
    label: "CYL",
    role: "SL",
    filter: "",
    subFilter: "SL-ST",
    title: "CYL | -12 | -11 | -10 |...",
    entityName: "products",
    fieldName: "cylinder",
    type: "select",
    placeholder: "Select CYL...",
    required: false,
    options: generateLensOptions(-12, 12),
  },
]

// Base Lens | Rx Lenses
export const RxLensVariantConfig: ProductConfigType[] = [
  {
    name: "lens_base_curve",
    label: "Lens Base Curve",
    role: "all",
    filter: "Base Curve",
    subFilter: "RX-CL",
    title: "Lens Base Curve",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    placeholder: "Select base curve...",
    required: true,
  },
  {
    name: "addition",
    label: "ADD",
    role: "SL",
    filter: "",
    subFilter: "SL-ST",
    title: "ADD | 1 | 2 | 3 |...",
    entityName: "products",
    fieldName: "addition",
    options: generateLensOptions(1, 6),
    type: "select",
    placeholder: "Select ADD...",
    required: false,
  },
]

// Base Lens | Stock Lenses + Rx Lenses
export const ContactLensVariantConfig: ProductConfigType[] = [
  {
    name: "lens_water_content",
    label: "Lens Water Content",
    role: "CL",
    filter: "Water Content",
    subFilter: "",
    title: "Lens Water Content | 12% | 13% | 14% |...",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    placeholder: "Select water content...",
    required: false,
  },
  {
    name: "replacement_schedule",
    label: "Replacement Schedule",
    role: "CL",
    filter: "Replacement Schedule",
    subFilter: "",
    title: "Replacement Schedule | Daily | Weekly | Monthly |...",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    placeholder: "Select schedule...",
    required: true,
  },
  {
    name: "units",
    label: "Unit",
    role: "CL",
    filter: "Unit",
    subFilter: "",
    title: "Items in box | 1piece | 2piece | 3piece |...",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    placeholder: "Select unit...",
    required: true,
  },
  {
    name: "axis",
    label: "AXIS",
    role: "SL",
    filter: "",
    subFilter: "SL-ST",
    title: "AXIS | 0 | 1 | 2 |...",
    entityName: "products",
    fieldName: "axis",
    options: generateLensOptions(0, 180, 1, false),
    type: "select",
    placeholder: "Select AXIS...",
    required: true,
  },
  {
    name: "expiration_date",
    label: "Expiration Date",
    role: "CL",
    filter: "Expiration Date",
    subFilter: "",
    title: "Expiration Date | YYYY-MM-DD |...",
    entityName: "",
    fieldName: "expiration_date",
    type: "date",
    placeholder: "Select Expiration Date...",
    required: true,
  },
]



export const CustomVariantMainConfig: ProductConfigType[]=[
  {
    name: "variant_type",
    label: "Product Variant Name",
    role: "all",
    filter: "",
    subFilter: "",
    title: "Variant Name Should be unique",
    entityName: "attribute",
    fieldName: "name",
    type: "foreignkey",
    // placeholder: "Select Attribute...",
    required: true,
  },
]


export const CustomVariantConfig: ProductConfigType[]=[
  {
    name: "attribute",
    label: "Attribute",
    role: "all",
    filter: "",
    subFilter: "",
    title: "attribute | ...",
    entityName: "attributes",
    fieldName: "name",
    type: "foreignkey",
    // placeholder: "",
    required: true,
  },
  {
    name: "value",
    label: "Value",
    role: "all",
    filter: "Value",
    subFilter: "",
    title: "Value | ...",
    entityName: "attribute-values",
    fieldName: "attribute_name",
    type: "foreignkey",
    // placeholder: "Select Value...",
    required: true,
  },

]


export const veriantConfig = (variant_type:string)=>{
    let config: any[] = [];
    switch (variant_type) {
        case "basic":
            config = BasicVariantConfig ;
            break;
        case "frames":
            config =  [ ...FrameVariantConfig, ...BasicVariantConfig];
            break;
        case "stockLenses":
            config = [ ...StockLensVariantConfig, ...BaseLensVariantConfig, ...BasicVariantConfig];
            break;
        case "rxLenses":
            config = [ ...RxLensVariantConfig, ...BaseLensVariantConfig, ...BasicVariantConfig];
            break;
        case "contactLenses":
            config = [ ...ContactLensVariantConfig, ...BaseLensVariantConfig, ...BasicVariantConfig];
            break;
        case "custom":
            config = BasicVariantConfig
            break;
        default:
            config = [];
            break;
    }
    return config;
}