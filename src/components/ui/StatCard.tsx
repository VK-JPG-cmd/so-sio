import React from 'react';
import { Card } from './Card';
import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  change?: {
    value: string;
    trend: 'up' | 'down' | 'neutral';
    label: string;
  };
  accentColor?: 'purple' | 'pink' | 'emerald' | 'rose' | 'amber' | 'blue' | 'dark' | 'yellow';
  subtitle?: string;
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon: Icon,
  change,
  accentColor = 'dark',
  subtitle,
  onClick,
}) => {
  const colorMap = {
    dark: {
      bg: 'bg-[#111312]',
      text: 'text-[#FBF5A5]',
      border: 'border-[#2B2D2C]',
    },
    yellow: {
      bg: 'bg-[#FBF5A5]',
      text: 'text-[#111312]',
      border: 'border-[#FBF5A5]',
    },
    purple: {
      bg: 'bg-[#111312]',
      text: 'text-[#FBF5A5]',
      border: 'border-[#2B2D2C]',
    },
    pink: {
      bg: 'bg-[#434346]',
      text: 'text-white',
      border: 'border-[#55555A]',
    },
    emerald: {
      bg: 'bg-[#EAF5F0]',
      text: 'text-[#2F7C5B]',
      border: 'border-[#C3E4D6]',
    },
    rose: {
      bg: 'bg-[#FDEEEF]',
      text: 'text-[#C8485E]',
      border: 'border-[#F5C4CB]',
    },
    amber: {
      bg: 'bg-[#FDF6E9]',
      text: 'text-[#B87B28]',
      border: 'border-[#F1DCBD]',
    },
    blue: {
      bg: 'bg-[#434346]',
      text: 'text-[#FBF5A5]',
      border: 'border-[#5A5A60]',
    },
  }[accentColor] || {
    bg: 'bg-[#111312]',
    text: 'text-[#FBF5A5]',
    border: 'border-[#2B2D2C]',
  };

  return (
    <Card
      hoverEffect={!!onClick}
      onClick={onClick}
      className="relative overflow-hidden transition-all bg-white border border-[#E2E1DC]"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold text-[#737478] uppercase tracking-wider">{title}</p>
          <h4 className="text-2xl sm:text-3xl font-extrabold text-[#111312] mt-1 tracking-tight">{value}</h4>
          {subtitle && <p className="text-xs text-[#737478] mt-1">{subtitle}</p>}
        </div>

        <div className={`p-2.5 rounded-xl ${colorMap.bg} ${colorMap.text} border ${colorMap.border} shadow-sm shrink-0`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      {change && (
        <div className="mt-4 pt-3 border-t border-[#EAE9E4] flex items-center gap-1.5 text-xs">
          <span className={`inline-flex items-center font-bold ${
            change.trend === 'up' ? (accentColor === 'rose' ? 'text-rose-600' : 'text-[#2F7C5B]') :
            change.trend === 'down' ? (accentColor === 'rose' ? 'text-[#2F7C5B]' : 'text-rose-600') : 'text-[#737478]'
          }`}>
            {change.trend === 'up' ? <TrendingUp className="w-3.5 h-3.5 mr-0.5" /> : 
             change.trend === 'down' ? <TrendingDown className="w-3.5 h-3.5 mr-0.5" /> : null}
            {change.value}
          </span>
          <span className="text-[#737478]">{change.label}</span>
        </div>
      )}
    </Card>
  );
};
