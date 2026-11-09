'use client';
import { Controller } from 'react-hook-form';
import ReactSelect from 'react-select';
import { RHFSelectProps } from '../types';
import customStyles from '@/src/shared/constants/customStyles';


export const RHFSelect = (props: RHFSelectProps) => {
  const { name, control, parsedOptions, label, required = false, placeholder = 'Select...', className = ''} = props;
  return (
    <div className={className}>
      <Controller
        name={name as any}
        control={control}
        rules={{
          required: required ? `${label || name} is required` : false,
        }}

        render={({ field, fieldState }) => (
          <>
            <ReactSelect
              inputId={name}
              options={parsedOptions}
              onChange={(opt) => {field.onChange((opt as any)?.value)}}
              onBlur={field.onBlur}
              value={parsedOptions.find((o) => o.value === field.value) || null}
              styles={customStyles}
              placeholder={placeholder}
              isClearable
            />
            {fieldState.error && (
              <p className="text-sm text-red-500 mt-1">
                {fieldState.error.message}
              </p>
            )}
          </>
        )}
      />
    </div>
  );
};
