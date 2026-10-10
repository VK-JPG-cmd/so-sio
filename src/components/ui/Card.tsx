import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  header?: React.ReactNode;
  footer?: React.ReactNode;
  variant?: 'light' | 'dark' | 'charcoal';
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  hoverEffect = false,
  padding = 'md',
  header,
  footer,
  variant = 'light',
  onClick,
}) => {
  const paddingStyles = {
    none: '',
    sm: 'p-4',
    md: 'p-5 sm:p-6',
    lg: 'p-6 sm:p-8',
  }[padding];

  const variantStyles = {
    light: 'bg-white text-[#111312] border border-[#E2E1DC]',
    dark: 'bg-[#181A19] text-[#F7F7F6] border border-[#2B2D2C]',
    charcoal: 'bg-[#434346] text-white border border-[#58585D]',
  }[variant];

  const hoverStyles = hoverEffect
    ? variant === 'dark'
      ? 'hover:border-[#FBF5A5]/60 hover:-translate-y-0.5 cursor-pointer transition-all duration-200'
      : 'hover:border-[#111312]/60 hover:shadow-solid hover:-translate-y-0.5 cursor-pointer transition-all duration-200'
    : '';

  const dividerBorder = variant === 'dark' ? 'border-[#2B2D2C]' : 'border-[#EAE9E4]';
  const footerBg = variant === 'dark' ? 'bg-[#131514]' : 'bg-[#FAF9F6]';

  return (
    <div
      onClick={onClick}
      className={`rounded-2xl sm:rounded-3xl shadow-sm transition-all duration-200 ${variantStyles} ${hoverStyles} ${className}`}
    >
      {header && (
        <div className={`px-5 sm:px-6 py-4 border-b ${dividerBorder} flex items-center justify-between`}>
          {header}
        </div>
      )}
      <div className={paddingStyles}>{children}</div>
      {footer && (
        <div className={`px-5 sm:px-6 py-3.5 ${footerBg} rounded-b-2xl sm:rounded-b-3xl border-t ${dividerBorder}`}>
          {footer}
        </div>
      )}
    </div>
  );
};
