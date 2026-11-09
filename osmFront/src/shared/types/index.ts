import { PageData } from "@/src/features/pages/types";
import { UseFormReturn, FieldValues } from "react-hook-form";

export type ApiError = {
    [field: string]: string | string[];
  };

  export type ApiSuccess = {
    [field: string]: string | string[];
  };
  

export interface FormApiOptions<T = any> {
  alias: string;
  onSuccess?: (res: any) => void;
  onError?: (err: any) => void;
  transform?: (data: any) => any;
}


export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: any;
}

//  ues in crud
export interface CrudFormOptions {
  alias: string;
  defaultValues?: any;
  onSuccess?: () => void;
  onError?: (err: any) => void;
  className?: string;
  submitText?: string;
}

//  ues in login and create and edit
export interface formRequestProps extends CrudFormOptions  {
  onCancel?: () => void;
  showCancelButton?: boolean;
  mode?: 'create' | 'edit'|'login';
  id?: string | number | undefined;
  submitForm?: (data?: any) => Promise<{ success: boolean; error?: any }>;
  istenant?: boolean;
  title?: string;
  message?: string;
  
}

export interface useFormRequestProps {
    alias?: string;
  defaultValues?: any;
  onSuccess?: (res: any) => void;
  onError?: (err: any) => void;
  transform?: (data: any) => any;
  showToast?: boolean;
  skipCache?: boolean;
  enabled?: boolean;

}

export type UseFormRequestReturn = {
  isSubmitting: boolean;
  errors: any;
  formErrors: any;
  submitForm: any;
  retry?: () => Promise<any>;
  reset?: (defaultValues?: any) => void;
  [key: string]: any; // للسماح بخصائص إضافية مثل methods الأخرى
};

export type UseApiFormReturn = UseFormReturn<any, any, any> & {
 query: any, // للـ GET
 mutation: any, // للـ POST/PUT/DELETE
 submitForm: any, // دالة submit موحدة
 isBusy: boolean,
 resetForm: () => void,
 prefetch: (newValues: any) => Promise<void>,
 fetchDirect: () => Promise<{ success: boolean; error?: any }>,
 errors: any,

};
export type UserContextType = {
  user: any | null;
  setUser: (user: any | null) => void;
  // fetchUser:UseFormRequestReturn;
  refetchUser: () => Promise<{ success: boolean; error?: any }>;
  loading: boolean;
  logout: () => Promise<void>;
};

export interface Permission {
  id: number;
  code: string;
  description: string;
}

export interface Role {
  id: number;
  name: string;
  permissions: Permission[];
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_staff: boolean;
  role: Role;
  is_deleted: boolean;
  deleted_at: string | null;
  phone: string;
  client: number;
}


export interface ViewCardProps {
  entity: string;
  id?: string | number | undefined;
}

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'success' | 'info' | 'outline' | 'link' | 'reset' | 'cancel' | 'close'| 'warning';


export interface ButtonProps {
  label?: string;
  variant?: ButtonVariant;
  icon?: React.ReactNode;
  className?: string;
  type?: "button" | "submit" | "reset";
  title?: string;
  disabled?: boolean;
  onCrud?: (e?: React.SyntheticEvent) => void | Promise<void>; // يقبل أي event
  navigateTo?: string;
  onClick?: (e?: React.SyntheticEvent) => void | Promise<void>; // يقبل أي event
  name?: string;
  entity?: string;
}



export interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}


// for render buttons
export interface Alias {
  deleteAlias: string;
  editAlias: string;
}


export type RenderButtonsProps = {
  data: PageData;
  alias: Alias;
  refetch: () => void;   // ✅ إضافة refetch
  navigatePath: string;
  isViweOnly?: boolean;
};



export interface DynamicFormDialogProps {
  onClose: (e: any) => void;
  entity: string;
  title?: string;
  defaultValues?: any;
}


export interface ConfirmDialogProps {
  open: boolean;
  title?: string;
  message?: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmText?: string;
  cancelText?: string;
  isDanger?: boolean;
}

export type GlobalAlertType = "info" | "warning" | "error" | "success";
export interface GlobalAlertProps {
  message?: string; // يمكن تمريرها من parent
  type?: GlobalAlertType; // يمكن تمريرها من parent
}


/**
 * Normalized error interface
 */
export interface NormalizedError {
  message: string;
  code?: number | string;
  details?: any;
}
