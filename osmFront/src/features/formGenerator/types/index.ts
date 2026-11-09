// types RHFSelect
export interface Option {
    value: string | number;
    label: string;
}

export interface RHFSelectProps {
    name: string;
    control: any;
    parsedOptions: Option[];
    label?: string;
    required?: boolean;
    placeholder?: string;
    className?: string;
}

interface baseFieldProps {
    fieldName: string;
    register: any;
    config: any;
    label: string;
    required: boolean;
    errors: any;
}    

export interface UnionFieldProps extends baseFieldProps {
    fieldSchema: any;
}



export interface ForeignKeyFieldProps extends baseFieldProps {
    form: any;
    setShowModal: (show: boolean) => void;
    fetchForginKey: boolean;
    setFetchForginKey: (fetch: boolean) => void;
}


