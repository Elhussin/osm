export type OptionType = { label: string; value: string | number };
export type OptionsProps = OptionType[];

export interface ProductConfigType {
  name: string;
  label?: string;
  role: string;
  filter: string;
  subFilter?: string;
  title?: string;
  entityName: string;
  fieldName: string;
  type?: string;
  placeholder?: string;
  required: boolean;
  options?: OptionsProps;
  mapOnly?: boolean;
  defaultValue?: any;
  className?: string;
}

export interface ProductForginKeyConfigType {
  name: string;
  label?: string;
  role: string;
  filter: string;
  subFilter?: string;
  title?: string;
  entityName: string;
  fieldName: string;
  type?: string;
  placeholder?: string;
  required: boolean;
  options?: OptionsProps;
  mapOnly?: boolean;
  defaultValue?: any;
  className?: string;
}

export interface RenderFormProps {
  fields: ProductConfigType[];
  form: any;
  options?: OptionsProps;
  selectedType?: string;
  variantNumber?: number;
  attributeIndex?: number;
}
// Fields
export interface FieldsProps {
  fieldRow: ProductConfigType;
  field: any;
}

export interface SelectFieldsProps extends FieldsProps {
  options?: OptionsProps;
}
// MultiSelectField
export interface MultiSelectFieldProps {
    fieldName: string;
    control: any;
    fieldRow: ProductConfigType;
    options: OptionsProps;
    
}


