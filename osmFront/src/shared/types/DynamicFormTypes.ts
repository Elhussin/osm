
export interface FieldTemplate {
  component: string;
  type?: string;
  props?: Record<string, any>;
  wrapper?: string;
}

export interface GeneratorConfig {
  baseClasses: string;
  labelClasses: string;
  errorClasses: string;
  submitButtonClasses: string;
  submitButtonText: string;
  includeResetButton: boolean;
  fieldOrder?: string[];
  spacing: string;
  containerClasses: string;
}

export interface DynamicFormProps{
  entity?: string;
  mode?: 'create' | 'edit';
  id?: string | number;
  setData?: (e: any) => void; 
  defaultValues?: any;
}

export interface ForeignKeyConfig {
  endpoint?: string;
  labelField: string;
  valueField: string;
  searchField?: string;
  createPage?: string;
  entityName: string;
}

export interface RelationshipConfig {
  [fieldName: string]: ForeignKeyConfig;

}
