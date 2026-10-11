import React from 'react';
import { ThreatSeverity, ThreatStatus } from '../../types';
import { ShieldCheck, ShieldAlert, AlertTriangle, AlertOctagon, CheckCircle2, Clock, Send, ShieldX, HelpCircle } from 'lucide-react';

interface BadgeProps {
  children?: React.ReactNode;
  variant?: 'severity' | 'status' | 'category' | 'outline' | 'neutral' | 'brand' | 'dark' | 'accent';
  severity?: ThreatSeverity;
  status?: ThreatStatus | string;
  className?: string;
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  severity,
  status,
  className = '',
  size = 'md'
}) => {
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs font-semibold';

  if (variant === 'severity' || severity) {
    const sev = severity || 'low';
    const config = {
      low: {
        bg: 'bg-[#EAF5F0] text-[#2F7C5B] border-[#C3E4D6]',
        icon: ShieldCheck,
        label: 'Low Risk'
      },
      medium: {
        bg: 'bg-[#FDF6E9] text-[#B87B28] border-[#F1DCBD]',
        icon: AlertTriangle,
        label: 'Medium Risk'
      },
      high: {
        bg: 'bg-[#FDEEEF] text-[#C8485E] border-[#F5C4CB]',
        icon: ShieldAlert,
        label: 'High Risk'
      },
      critical: {
        bg: 'bg-[#111312] text-[#FBF5A5] border-[#434346]',
        icon: AlertOctagon,
        label: 'Critical Risk'
      },
    }[sev];

    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full border ${config.bg} ${sizeClasses} ${className}`}>
        <Icon className="w-3 h-3 shrink-0" />
        <span>{children || config.label}</span>
      </span>
    );
  }

  if (variant === 'status' || status) {
    const st = status || 'active';
    const config: Record<string, { bg: string; icon: any; label: string }> = {
      active: {
        bg: 'bg-[#FDEEEF] text-[#C8485E] border-[#F5C4CB]',
        icon: ShieldAlert,
        label: 'Active Threat'
      },
      under_investigation: {
        bg: 'bg-[#222423] text-[#FBF5A5] border-[#3E403F]',
        icon: Clock,
        label: 'Being reviewed'
      },
      takedown_requested: {
        bg: 'bg-[#434346] text-white border-[#5A5A60]',
        icon: Send,
        label: 'Removal requested'
      },
      resolved: {
        bg: 'bg-[#EAF5F0] text-[#2F7C5B] border-[#C3E4D6]',
        icon: CheckCircle2,
        label: 'Resolved / Removed'
      },
      false_positive: {
        bg: 'bg-[#EFEFEA] text-[#434346] border-[#DCDAD4]',
        icon: ShieldX,
        label: 'Safe / Allowed'
      },
      verified: {
        bg: 'bg-[#FBF5A5] text-[#111312] border-[#FBF5A5] font-bold',
        icon: ShieldCheck,
        label: 'Verified Official'
      },
      pending: {
        bg: 'bg-[#FDF6E9] text-[#B87B28] border-[#F1DCBD]',
        icon: Clock,
        label: 'Pending Verification'
      }
    };

    const current = config[st] || {
      bg: 'bg-[#EFEFEA] text-[#111312] border-[#DCDAD4]',
      icon: HelpCircle,
      label: st
    };

    const Icon = current.icon;

    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full border ${current.bg} ${sizeClasses} ${className}`}>
        <Icon className="w-3 h-3 shrink-0" />
        <span>{children || current.label}</span>
      </span>
    );
  }

  if (variant === 'brand' || variant === 'accent') {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full bg-[#FBF5A5] text-[#111312] border border-[#FBF5A5] font-bold ${sizeClasses} ${className}`}>
        {children}
      </span>
    );
  }

  if (variant === 'dark') {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full bg-[#222423] text-[#F7F7F6] border border-[#3E403F] ${sizeClasses} ${className}`}>
        {children}
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1 rounded-full bg-[#EFEFEA] text-[#111312] border border-[#DCDAD4] text-xs font-medium ${sizeClasses} ${className}`}>
      {children}
    </span>
  );
};
