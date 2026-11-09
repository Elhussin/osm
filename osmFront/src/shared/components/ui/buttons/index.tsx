"use client";
import React from "react";
import { cn } from "@/src/shared/utils/cn"; 
import { ButtonProps } from "@/src/shared/types";
import { useRouter } from "@/src/app/i18n/navigation";

  const variantClasses = {
    primary: "btn-primary",
    secondary: "btn-secondary",
    danger: "btn-danger",
    success: "btn-success",
    info: "btn-info",
    outline: "btn-outline",
    link: "btn-link",
    reset: "btn-reset",
    cancel: "btn-cancel",
    close: "btn-close",
    warning: "btn-warning",

  };



export function ActionButton({
  label = "",
  icon,
  variant = "primary",
  className = "",
  type = "button",
  title = "",
  disabled,
  onClick,
  onCrud,
  navigateTo,
  name,

}: ButtonProps) {
  const router = useRouter();

  const handleClick = async (e: React.MouseEvent<HTMLButtonElement>) => {
    // لو الزر submit → نسيب التحكم للفورم (preventDefault هيتعامل معه هناك)
    if (type === "submit") {
      if (onClick) await onClick(e); // لو حابب تضيف extra logic مع submit
      // return;
    }

    // لو onClick موجود → ننفذه
    if (onClick) await onClick(e);

    // لو onCrud موجود → ننفذه
    if (onCrud) await onCrud(e);

    // لو في navigation → ننفذه
    if (navigateTo) router.push(navigateTo);
  };

  return (
    <button
      onClick={handleClick}
      type={type}
      name={name!}
      // entity={entity!}
      title={title}
      disabled={disabled}
      className={cn(
        "btn flex items-center justify-center gap-1", // ⚡ flex + center
        variantClasses[variant],
        className
      )}
    >
      {icon}
      {label && <span>{label}</span>}
    </button>
  );
  
}
