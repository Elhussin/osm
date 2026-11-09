// scripts/generate-zod-form.ts

import fs from 'fs';
import path from 'path';
// import { schemas } from '../shared/lib/schemas';
import { schemas } from '@/src/shared/api/schemas'
// C:\coding\optics_tenant\osmFront\src\shared\api\schemas.ts
import { z } from 'zod';

// ===== configuration and settings =====
interface GeneratorConfig {
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

interface FieldTemplate {
  component: string;
  type?: string;
  props?: Record<string, any>;
  wrapper?: string;
}

const defaultConfig: GeneratorConfig = {
  baseClasses: "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
  labelClasses: "block text-sm font-medium text-gray-700 mb-1",
  errorClasses: "text-red-500 text-sm mt-1",
  submitButtonClasses: "bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md font-medium transition-colors",
  submitButtonText: "Save",
  includeResetButton: false,
  spacing: "mb-4",
  containerClasses: "space-y-4"
};

const fieldTemplates: Record<string, FieldTemplate> = {
  'email': { component: 'input', type: 'email' },
  'password': { component: 'input', type: 'password' },
  'url': { component: 'input', type: 'url' },
  'tel': { component: 'input', type: 'tel' },
  'number': { component: 'input', type: 'number' },
  'date': { component: 'input', type: 'date' },
  'datetime': { component: 'input', type: 'datetime-local' },
  'time': { component: 'input', type: 'time' },
  'textarea': { component: 'textarea', props: { rows: 3 } },
  'select': { component: 'select' },
  'checkbox': { component: 'input', type: 'checkbox', wrapper: 'checkbox' },
  'radio': { component: 'input', type: 'radio', wrapper: 'radio' },
  'file': { component: 'input', type: 'file' },
  'color': { component: 'input', type: 'color' },
  'range': { component: 'input', type: 'range' }
};

// command line arguments
const [, , schemaName, apiEndpoint, configPath] = process.argv;

// check if schema name is provided
if (!schemaName || !(schemaName in schemas)) {
  console.error('❌ Please provide a valid schema name from zodSchemas.ts');
  console.log('Available schemas:', Object.keys(schemas).join(', '));
  process.exit(1);
}
// load config
let config: GeneratorConfig = defaultConfig;
if (configPath && fs.existsSync(configPath)) {
  const userConfig = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  config = { ...defaultConfig, ...userConfig };
}

// set api endpoint
const YOUR_ENDPOINT = apiEndpoint || 'YOUR_ENDPOINT';
const schema = (schemas as any)[schemaName] as z.ZodObject<any>;
const shape = schema.shape;

// ignore fields

const ignoredFields = ['id', 'created_at', 'updated_at', 'owner', 'tenant', '', 'group'];
const allFields = Object.keys(shape).filter((f) => !ignoredFields.includes(f));
const visibleFields = config.fieldOrder || allFields;

// generate file names
const pascal = schemaName.replace(/(^\w|_\w)/g, (m) => m.replace('_', '').toUpperCase());
const camel = schemaName.replace(/_(\w)/g, (_, c) => c.toUpperCase());

// helper functions
function unwrapSchema(schema: z.ZodTypeAny): z.ZodTypeAny {
  while (
    schema instanceof z.ZodOptional ||
    schema instanceof z.ZodNullable ||
    schema instanceof z.ZodDefault
  ) {
    schema = (schema as any)._def.innerType;
  }
  return schema;
}

// detect field type
function detectFieldType(field: string, rawSchema: z.ZodTypeAny): string {
  const schema = unwrapSchema(rawSchema);

  // analyze field name
  const fieldLower = field.toLowerCase();
  if (fieldLower.includes('email')) return 'email';
  if (fieldLower.includes('password')) return 'password';
  if (fieldLower.includes('phone') || fieldLower.includes('tel')) return 'tel';
  if (fieldLower.includes('url') || fieldLower.includes('website')) return 'url';
  if (fieldLower.includes('color')) return 'color';
  if (fieldLower.includes('date')) return 'date';
  if (fieldLower.includes('time')) return 'time';
  if (fieldLower.includes('description') || fieldLower.includes('content') || fieldLower.includes('notes')) return 'textarea';

  // analyze schema type
  if (schema instanceof z.ZodBoolean) return 'checkbox';
  if (schema instanceof z.ZodEnum) return 'select';
  if (schema instanceof z.ZodNumber) return 'number';

  if (schema instanceof z.ZodString) {
    const checks = schema._def.checks || [];
    const hasEmail = checks.some((c: any) => c.kind === 'email');
    const hasUrl = checks.some((c: any) => c.kind === 'url');
    const hasMinLength = checks.some((c: any) => c.kind === 'min' && c.value >= 6);
    const hasMaxLength = checks.some((c: any) => c.kind === 'max' && c.value > 100);

    if (hasEmail) return 'email';
    if (hasUrl) return 'url';
    if (hasMinLength && fieldLower.includes('password')) return 'password';
    if (hasMaxLength) return 'textarea';
  }

  if (schema instanceof z.ZodArray) return 'array';
  if (schema instanceof z.ZodObject) return 'object';

  return 'text';
}

// generate field code
function generateFieldCode(field: string, rawSchema: z.ZodTypeAny): string {
  const fieldType = detectFieldType(field, rawSchema);
  const template = fieldTemplates[fieldType] || fieldTemplates['text'] || { component: 'input', type: 'text' };
  const schema = unwrapSchema(rawSchema);
  const description = rawSchema.description || field.replace(/_/g, ' ').replace(/^\w/, c => c.toUpperCase());
  const isRequired = !(rawSchema instanceof z.ZodOptional);

  let inputElement = '';
  let wrapperStart = '';
  let wrapperEnd = '';

  // معالجة wrapper خاص
  if (template.wrapper === 'checkbox') {
    wrapperStart = `<div className="flex items-center space-x-2">`;
    wrapperEnd = `</div>`;
    inputElement = `
      <input 
        id="${field}" 
        type="checkbox" 
        {...register("${field}")} 
        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" 
      />
      <label htmlFor="${field}" className="${config.labelClasses}">${description}</label>`;
  } else {
    // Label عادي
    const labelElement = `<label htmlFor="${field}" className="${config.labelClasses}">
      ${description}${isRequired ? ' *' : ''}
    </label>`;

    // Input element بناء على النوع
    switch (fieldType) {
      case 'select':
        if (schema instanceof z.ZodEnum) {
          const options = schema.options
            .map((opt: any) => `<option value="${opt}">${opt}</option>`)
            .join('\n      ');
          inputElement = `${labelElement}
    <select 
      id="${field}" 
      {...register("${field}")} 
      className="${config.baseClasses}"
    >
      <option value="">اختر...</option>
      ${options}
    </select>`;
        }
        break;

      case 'textarea':
        const rows = template.props?.rows || 3;
        inputElement = `${labelElement}
    <textarea 
      id="${field}" 
      {...register("${field}")} 
      className="${config.baseClasses}" 
      rows={${rows}}
      placeholder="${description}..."
    />`;
        break;

      case 'array':
        inputElement = `${labelElement}
    <div className="space-y-2">
      {/* Array field - needs custom implementation */}
      <input 
        id="${field}" 
        type="text" 
        {...register("${field}")} 
        className="${config.baseClasses}" 
        placeholder="Comma-separated values"
      />
    </div>`;
        break;

      case 'object':
        inputElement = `${labelElement}
    <div className="border border-gray-200 rounded-md p-3">
      {/* Nested object - needs custom implementation */}
      <input 
        id="${field}" 
        type="text" 
        {...register("${field}")} 
        className="${config.baseClasses}" 
        placeholder="JSON object"
      />
    </div>`;
        break;

      default:
        const inputType = template.type || 'text';
        const additionalProps = template.props ? Object.entries(template.props)
          .map(([key, value]) => `${key}={${JSON.stringify(value)}}`)
          .join(' ') : '';

        inputElement = `${labelElement}
    <input 
      id="${field}" 
      type="${inputType}" 
      {...register("${field}")} 
      className="${config.baseClasses}" 
      placeholder="${description}..."
      ${additionalProps}
    />`;
    }
  }

  return `
  <div className="${config.spacing}">
    ${wrapperStart}
    ${inputElement}
    ${wrapperEnd}
    {errors.${field} && <p className="${config.errorClasses}">{errors.${field}?.message}</p>}
  </div>`;
}


// Form Component
const formCode = `// components/forms/${pascal}Form.tsx
import React from 'react';
import { schemas } from '@/lib/zod-client';
import { useFormRequest } from '@/lib/hooks/useFormRequest';
import { toast } from 'sonner';
import { handleErrorStatus } from '@/utils/error';
import { z } from 'zod';
import { CreateUserType } from '@/types';
const schema = schemas.${schemaName};

export default function ${pascal}Form({
  onSuccess,
  onCancel,
  defaultValues,
  className = "",
  submitText = "${config.submitButtonText}",
  showCancelButton = false,
  mode = 'create',
  id,
  ...options
}: CreateUserType) {
  const { 
    register, 
    handleSubmit, 
    formState: { errors, isSubmitting }, 
    submitForm,
    reset
  } =useFormRequest(schema,{ mode, id, defaultValues, apiOptions: { endpoint: '${YOUR_ENDPOINT}', onSuccess: (res) => onSuccess?.(res), }});

  const onSubmit = async (data: z.infer<typeof schema>) => {
    try {
      const result = await submitForm(data);
      onSuccess?.(result);
      if (mode === 'create') {
        reset();
      }
    } catch (error: any) {
      if (error.response?.data) {
        const errorData = error.response.data;
        if (typeof errorData === 'object') {
          // عرض جميع رسائل الخطأ
          Object.entries(errorData).forEach(([field, messages]) => {
            if (Array.isArray(messages)) {
              messages.forEach(message => toast.error(\`\${field}: \${message}\`));
            } else {
              toast.error(\`\${field}: \${messages}\`);
            }
          });
        } else {
          toast.error(errorData);
        }
      } else {
        toast.error(handleErrorStatus(error));
      }
      console.error('Form submission error:', error);
    }
  };

  return (
    <div className={\`\${className}\`}>
      <form onSubmit={handleSubmit(onSubmit)} className="${config.containerClasses}">
        ${visibleFields.map((f) => generateFieldCode(f, shape[f])).join('\n')}
        
        <div className="flex gap-3 pt-4">
          <button 
            type="submit" 
            disabled={isSubmitting}
            className={\`${config.submitButtonClasses} \${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}\`}
            disabled={mode === 'edit' && fieldName === 'email'||mode === 'edit' && fieldName === 'username'||mode === 'edit' && fieldName === 'password'}
            
            >
            {isSubmitting ? 'Saving...' : submitText}
          </button>
          
          ${config.includeResetButton ? `
          <button 
            type="button" 
            onClick={() => reset()}
            className="bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-md font-medium transition-colors"
          >
            Reset
          </button>` : ''}
          
          {showCancelButton && (
            <button 
              type="button" 
              onClick={onCancel}
              className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-6 py-2 rounded-md font-medium transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
`;



// ===== write files =====
const formFile = `src/features/formGenerator/components/${pascal}Form.tsx`;


// create directories
fs.mkdirSync(path.dirname(formFile), { recursive: true });
fs.writeFileSync(formFile, formCode)

console.log(`✅ ${pascal}Form created successfully:
📁 Form Component: ${formFile}
`);

// npx ts-node scripts/generate-zod-form.ts user_schema users/login
// npx tsx scripts/generate-zod-form.ts LoginRequest users/login ./config/custom-form.json
// npx tsx scripts/generate-zod-form.ts LogoutResponse users/logout ./config/custom-form.json
// npx tsx scripts/gen-zod.ts ProductRequest products/product ./config/custom-form.json


// z.custom<File>().refine(f => f instanceof File, { message: "Must be a File" }