import React from 'react';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'accent' | 'outline' | 'ghost' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles = "inline-flex items-center justify-center font-medium transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-[#111312]/30 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none select-none tracking-tight";

  const sizeStyles = {
    sm: "px-3 py-1.5 text-xs rounded-xl gap-1.5 font-semibold",
    md: "px-4 py-2 text-sm rounded-xl gap-2 font-semibold",
    lg: "px-6 py-3 text-base rounded-2xl gap-2.5 font-bold",
  }[size];

  const variantStyles = {
    primary: "bg-[#111312] hover:bg-[#232524] text-white hover:text-[#FBF5A5] border border-[#2B2D2C] shadow-sm",
    secondary: "bg-[#434346] hover:bg-[#343437] text-white border border-[#525256] shadow-sm",
    accent: "bg-[#FBF5A5] hover:bg-[#F6EF8A] text-[#111312] border border-[#FBF5A5] shadow-sm font-bold",
    outline: "bg-white hover:bg-[#F8F7F4] text-[#111312] border border-[#D5D4CE] hover:border-[#111312] shadow-sm",
    ghost: "bg-transparent hover:bg-[#EFEFEA] text-[#434346] hover:text-[#111312]",
    danger: "bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200",
    success: "bg-[#2F7C5B] hover:bg-[#26684C] text-white border border-[#2F7C5B] shadow-sm",
  }[variant];

  return (
    <button
      className={`${baseStyles} ${sizeStyles} ${variantStyles} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <Loader2 className="w-4 h-4 animate-spin shrink-0" />}
      {!isLoading && leftIcon}
      <span>{children}</span>
      {!isLoading && rightIcon}
    </button>
  );
};
