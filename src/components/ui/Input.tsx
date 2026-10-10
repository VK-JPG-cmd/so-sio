import React, { forwardRef } from 'react';
import { Search } from 'lucide-react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  className = '',
  id,
  ...props
}, ref) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className="w-full space-y-1.5">
      {label && (
        <label htmlFor={inputId} className="block text-xs font-bold text-[#111312] tracking-tight">
          {label}
        </label>
      )}
      <div className="relative flex items-center">
        {leftIcon && (
          <div className="absolute left-3.5 text-[#737478] flex items-center pointer-events-none">
            {leftIcon}
          </div>
        )}
        <input
          id={inputId}
          ref={ref}
          className={`w-full rounded-xl bg-white border border-[#DCDAD4] px-3.5 py-2.5 text-sm text-[#111312] placeholder:text-[#9A9B9C] transition-all duration-150 focus:outline-none focus:border-[#111312] focus:ring-2 focus:ring-[#FBF5A5] disabled:bg-[#EFEFEA] disabled:cursor-not-allowed ${
            leftIcon ? 'pl-10' : ''
          } ${rightIcon ? 'pr-10' : ''} ${
            error ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-200' : ''
          } ${className}`}
          {...props}
        />
        {rightIcon && (
          <div className="absolute right-3.5 text-[#737478] flex items-center">
            {rightIcon}
          </div>
        )}
      </div>
      {error && <p className="text-xs text-rose-600 font-semibold">{error}</p>}
      {helperText && !error && <p className="text-xs text-[#737478]">{helperText}</p>}
    </div>
  );
});

Input.displayName = 'Input';

interface SearchInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  onClear?: () => void;
}

export const SearchInput: React.FC<SearchInputProps> = ({
  placeholder = 'Search domains, threats, brands...',
  className = '',
  ...props
}) => {
  return (
    <Input
      type="text"
      placeholder={placeholder}
      leftIcon={<Search className="w-4 h-4" />}
      className={`bg-[#F4F3EF] border-[#DCDAD4] focus:bg-white ${className}`}
      {...props}
    />
  );
};

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(({
  label,
  error,
  helperText,
  className = '',
  id,
  ...props
}, ref) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className="w-full space-y-1.5">
      {label && (
        <label htmlFor={inputId} className="block text-xs font-bold text-[#111312] tracking-tight">
          {label}
        </label>
      )}
      <textarea
        id={inputId}
        ref={ref}
        rows={4}
        className={`w-full rounded-xl bg-white border border-[#DCDAD4] px-3.5 py-3 text-sm text-[#111312] placeholder:text-[#9A9B9C] transition-all duration-150 focus:outline-none focus:border-[#111312] focus:ring-2 focus:ring-[#FBF5A5] resize-y disabled:bg-[#EFEFEA] ${
          error ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-200' : ''
        } ${className}`}
        {...props}
      />
      {error && <p className="text-xs text-rose-600 font-semibold">{error}</p>}
      {helperText && !error && <p className="text-xs text-[#737478]">{helperText}</p>}
    </div>
  );
});

Textarea.displayName = 'Textarea';
