"use client";
import { useState } from "react";
import { Checkbox } from "@/src/shared/components/shadcn/ui/checkbox";
import { Switch } from "@/src/shared/components/shadcn/ui/switch";
import {
  RadioGroup,
  RadioGroupItem,
} from "@/src/shared/components/shadcn/ui/radio-group";
import {
  FormItem,
  FormControl,
  FormLabel,
} from "@/src/shared/components/shadcn/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/src/shared/components/shadcn/ui/select";
import { Input } from "@/src/shared/components/shadcn/ui/input";
import { Textarea } from "@/src/shared/components/shadcn/ui/textarea";
import { Button } from "@/src/shared/components/shadcn/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/src/shared/components/shadcn/ui/popover";
import {
  Command,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
} from "@/src/shared/components/shadcn/ui/command";
import { Check, ChevronsUpDown, X } from "lucide-react";
import { cn } from "@/src/shared/utils/cn";
import {
  FieldsProps,
  SelectFieldsProps,
  MultiSelectFieldProps,
} from "@/src/features/products/types";
import { Badge } from "@/src/shared/components/shadcn/ui/badge";
import { useForm, Controller } from "react-hook-form";
import { StringToBoolean } from "class-variance-authority/types";

export const CheckboxField = ({ fieldRow, field }: FieldsProps) => {
  return (
    <div className="flex items-center space-x-2">
      <Checkbox checked={field.value} onCheckedChange={field.onChange} />
      <span>{fieldRow.placeholder}</span>
    </div>
  );
};

export const SwitchField = ({ fieldRow, field }: FieldsProps) => {
  return (
    <div className="flex justify-between items-center border p-2 rounded-md">
      <span>{fieldRow.placeholder}</span>
      <Switch checked={field.value} onCheckedChange={field.onChange} />
    </div>
  );
};

export const RadioField = ({ fieldRow, field }: FieldsProps) => {
  return (
    <RadioGroup
      onValueChange={field.onChange}
      value={field.value}
      className="flex gap-3"
    >
      {(fieldRow.options || []).map((opt) => (
        <FormItem
          key={String(opt.value)}
          className="flex items-center space-x-2"
        >
          <FormControl>
            <RadioGroupItem value={String(opt.value)} />
          </FormControl>
          <FormLabel className="!mt-0">{opt.label}</FormLabel>
        </FormItem>
      ))}
    </RadioGroup>
  );
};

export const TextField = ({ fieldRow, field }: FieldsProps) => {
  return (
    <Input
      type={fieldRow.type}
      placeholder={fieldRow.placeholder}
      value={field.defaultValue || ""}
      {...field}
      className={fieldRow.className}
    />
  );
};

export const TextareaField = ({ fieldRow, field }: FieldsProps) => {
  return (
    <Textarea
      placeholder={fieldRow.placeholder}
      {...field}
      className="w-full"
      required={fieldRow.required}
    />
  );
};

export const SelectField = ({
  fieldRow,
  field,
  options,
}: SelectFieldsProps) => {
  return (
    <Select onValueChange={field.onChange} value={field.value}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder={fieldRow.placeholder || "Select"} />
      </SelectTrigger>
      <SelectContent>
        {(options || fieldRow.options || [{ value: "", label: "" }]).map(
          (opt: any, index: number) => (
            <SelectItem key={index} value={opt.value}>
              {opt.label}
            </SelectItem>
          )
        )}
      </SelectContent>
    </Select>
  );
};

// لاحظ أننا نحذف useState للـ value لأنها ستأتي من form
export function SearchableSelect({
  fieldRow,
  options,
  field,
}: SelectFieldsProps) {
  const [open, setOpen] = useState(false);
  const selectedLabel = options?.find((o) => o.value === field.value)?.label;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between"
        >
          {selectedLabel || fieldRow.placeholder || "Select..."}
          <ChevronsUpDown className="opacity-50 h-4 w-4" />
        </Button>
      </PopoverTrigger>

      <PopoverContent className="w-full p-0">
        <Command>
          <CommandInput placeholder="Search..." />
          <CommandList>
            <CommandEmpty>No results found.</CommandEmpty>
            <CommandGroup>
              {options?.map((opt, index) => (
                <CommandItem
                  key={index}
                  value={String(opt.value)}
                  onSelect={() => {
                    field.onChange(opt.value); // 🔹 نحدث القيمة في الـ form
                    setOpen(false);
                  }}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      field.value === opt.value ? "opacity-100" : "opacity-0"
                    )}
                  />
                  {opt.label}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

export const MultiCheckbox = ({
  fieldName,
  fieldRow,
  control,
  options,
}: MultiSelectFieldProps) => {
  // console.log("MultiCheckbox", options)
  const DefaultOptions = options || fieldRow.options || [];
  return (
    <Controller
      name={fieldName}
      control={control}
      defaultValue={[]as any} // ✅ يضمن أن field.value يكون [] وليس undefined
      render={({ field }) => (
        <div className="space-y-2 grid grid-cols-3 gap-1.5">
          {DefaultOptions?.map((opt: any, index: number) => (
            <div key={index} className="flex items-center space-x-2">
              <Checkbox
                id={opt.value}
                checked={(field.value || []).includes(opt.value)} // ✅ حماية إضافية
                onCheckedChange={(checked) => {
                  const currentValues = field.value || [];
                  const newValue = checked
                    ? [...currentValues, opt.value]
                    : currentValues.filter((v: string) => v !== opt.value);
                  field.onChange(newValue);
                }}
              />
              <label htmlFor={opt.value} className="text-sm font-medium">
                {opt.label}
              </label>
            </div>
          ))}
        </div>
      )}
    />
  );
};

export function MultiSelectField({
  control,
  fieldName,
  options,
}: MultiSelectFieldProps) {
  return (
    <Controller
      name={fieldName}
      control={control}
      defaultValue={[] as any} // ✅ يضمن أن field.value لن يكون undefined
      render={({ field }) => {
        const value = (field.value || []) as Array<string | number>;

        const selected =
          options?.filter((opt: any) => value.includes(opt.value)) || [];

        return (
          <div className="flex flex-col gap-2">
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className="w-full justify-between text-left font-normal"
                  type="button"
                >
                  {selected.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {selected.map((s) => (
                        <Badge
                          key={s.value}
                          className="text-xs flex items-center gap-1"
                        >
                          {s.label}
                          <X
                            className="w-3 h-3 cursor-pointer"
                            onClick={(e) => {
                              e.stopPropagation();
                              field.onChange(
                                value.filter((v) => v !== s.value)
                              );
                            }}
                          />
                        </Badge>
                      ))}
                    </div>
                  ) : (
                    <span className="text-muted-foreground">
                      Select options...
                    </span>
                  )}
                  <div className="flex items-center gap-1">
                    {selected.length > 0 && (
                      <span className="text-xs text-muted-foreground">
                        ({selected.length})
                      </span>
                    )}
                    <ChevronsUpDown className="w-4 h-4 opacity-50" />
                  </div>
                </Button>
              </PopoverTrigger>

              <PopoverContent className="p-0 w-[250px]">
                <Command>
                  <CommandList>
                    <CommandGroup>
                      {options?.map((opt) => (
                        <CommandItem
                          key={opt.value}
                          onSelect={() => {
                            const newValue = value.includes(opt.value)
                              ? value.filter((v) => v !== opt.value)
                              : [...value, opt.value];
                            field.onChange(newValue);
                          }}
                        >
                          <Check
                            className={cn(
                              "mr-2 h-4 w-4",
                              value.includes(opt.value)
                                ? "opacity-100"
                                : "opacity-0"
                            )}
                          />
                          {opt.label}
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
          </div>
        );
      }}
    />
  );
}
