// scripts/generate-zod-form.ts

import fs from 'fs';
import path from 'path';
import { schemas } from '@/src/shared/api/schemas';
import { z } from 'zod';

const [, , schemaName] = process.argv;
if (!schemaName || !(schemaName in schemas)) {
  console.error('❌ Please provide a valid schema name from zodSchemas.ts');
  process.exit(1);
}
const YOUR_ENDPOINT = process.argv[3] || 'YOUR_ENDPOINT'

const schema = (schemas as any)[schemaName] as z.ZodObject<any>;
const shape = schema.shape;

// 👇 تجاهل الحقول غير الضرورية
const ignoredFields = ['id', 'created_at', 'updated_at', 'owner', 'tenant', 'is_superuser', 'is_active', 'group'];
const visibleFields = Object.keys(shape).filter((f) => !ignoredFields.includes(f));

const pascal = schemaName.replace(/(^\w|_\w)/g, (m) => m.replace('_', '').toUpperCase());
const formFile = `src/components/forms/${pascal}Form.tsx`;
const hookFile = `src/lib/forms/use${pascal}Form.ts`;

function unwrapSchema(schema: z.ZodTypeAny): z.ZodTypeAny {
  while (
    schema instanceof z.ZodOptional ||
    schema instanceof z.ZodNullable ||
    schema instanceof z.ZodDefault
  ) {
    schema = schema._def.innerType as z.ZodTypeAny;
  }
  return schema;
}

function getFieldCode(field: string, rawSchema: z.ZodTypeAny): string {
  const baseClasses = `"input-base"`;
  const schema = unwrapSchema(rawSchema);
  const description = rawSchema.description || field;

  let inputElement = '';

  if (schema instanceof z.ZodBoolean) {
    inputElement = `
    <label htmlFor="${field}" className="inline-flex items-center space-x-2">
      <input id="${field}" type="checkbox" {...register("${field}")} />
      <span>${description}</span>
    </label>`;
  } else if (schema instanceof z.ZodEnum) {
    const options = schema.options
      .map((opt: any) => `<option value="${opt}">${opt}</option>`)
      .join('\n    ');
    inputElement = `
    <label htmlFor="${field}" className="block text-sm font-medium mb-1">${description}</label>
    <input 
      id="${field}" 
      list="${field}-list" 
      {...register("${field}")} 
      className=${baseClasses}
      placeholder="Type or select..."
    />
    <datalist id="${field}-list">
      ${options}
    </datalist>`;
  } else if (schema instanceof z.ZodNumber) {
    inputElement = `
    <label htmlFor="${field}" className="block text-sm font-medium mb-1">${description}</label>
    <input id="${field}" type="number" {...register("${field}")} className=${baseClasses} />`;
  } else if (schema instanceof z.ZodString) {
    const checks = schema._def.checks || [];
    const hasEmail = checks.some((c: any) => c.kind === 'email');
    const hasMinLength = checks.some((c: any) => c.kind === 'min' && c.value >= 6);
    let inputType = 'text';
    if (hasEmail) inputType = 'email';
    else if (hasMinLength) inputType = 'password';

    inputElement = `
    <label htmlFor="${field}" className="block text-sm font-medium mb-1">${description}</label>
    <input id="${field}" type="${inputType}" {...register("${field}")} className=${baseClasses} />`;
  } else {
    inputElement = `
    <label htmlFor="${field}" className="block text-sm font-medium mb-1">${description}</label>
    <input id="${field}" type="text" {...register("${field}")} className=${baseClasses} />`;
  }

  return `
  <div className="mb-4">
    ${inputElement}
    {form.formState.errors.${field} && <p className="text-red-500 text-sm">{form.formState.errors.${field}.message}</p>}
  </div>`;
}



const formCode = `import { use${pascal}Form } from '@/src/lib/forms/use${pascal}Form';
import { API } from '@/src/lib/api';

export default function ${pascal}Form({ defaultValues, onSuccess }: any) {
  const { register, handleSubmit, formState: { errors }, handleServerErrors } = use${pascal}Form(defaultValues);

  const onSubmit = async (data: any) => {
    try {
      await API.post('/api/${YOUR_ENDPOINT}/', data);
      onSuccess?.();
    } catch (e: any) {
      if (e.response?.status === 400) {
        handleServerErrors(e.response.data);
      }
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      ${visibleFields.map((f) => getFieldCode(f, shape[f])).join('\n')}
      <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">Save</button>
    </form>
  );
}
`;

const hookCode = `import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { schemas } from '@/src/api-zod/zodSchemas';

const schema = schemas.${schemaName};

export function use${pascal}Form(defaultValues?: Partial<z.infer<typeof schema>>) {
  const methods = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues,
  });

  const handleServerErrors = (apiErrors: any) => {
    Object.entries(apiErrors).forEach(([field, messages]) => {
      methods.setError(field as any, {
        type: 'server',
        message: messages[0],
      });
    });
  };

  return {
    ...methods,
    handleServerErrors,
  };
}
`;

fs.mkdirSync(path.dirname(formFile), { recursive: true });
fs.mkdirSync(path.dirname(hookFile), { recursive: true });

fs.writeFileSync(formFile, formCode);
fs.writeFileSync(hookFile, hookCode);

console.log(`✅ ${pascal}Form created successfully :
- ${formFile}
- ${hookFile}`);


// npx ts-node scripts/generate-zod-form.ts PrescriptionRecordRequest prescriptions
//  npx tsx scripts/generate-form.ts UserRequest users/register
// npx tsx scripts/generate-form.ts LoginRequest users/login
// npx tsx scripts/generate-form.ts PrescriptionRecordRequest prescriptions