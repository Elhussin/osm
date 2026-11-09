"use client"
import { z } from "zod";
import { unwrapSchema } from "../utils/unwrapSchema";
import { getUnionOptions } from "../utils/getUnionOptions";
import { UnionFieldProps } from "../types";

export function UnionField(props: UnionFieldProps) {
    const { fieldName, fieldSchema, register, config, label, required, errors } = props;
    const unwrappedSchema = unwrapSchema(fieldSchema);
    const options =
        unwrappedSchema instanceof z.ZodUnion
            ? getUnionOptions(unwrappedSchema)
            : [];

    return (
        <div className={`flex items-center gap-2 ${config.spacing}`}>
            <label htmlFor={fieldName} className={config.labelClasses}>
                {label}{required ? ' *' : ''}
            </label>
            <select
                id={fieldName}
                {...register(fieldName)}
                className={config.baseClasses}
            >
                <option value="" className="option">Select...</option>
                {options.map((option: string) => (
                    <option className="option" key={option} value={option}>
                        {option}
                    </option>
                ))}
            </select>
            {errors[fieldName] && (
                <p className={config.errorClasses}>
                    {errors[fieldName]?.message}
                </p>
            )}
        </div>
    );
}

