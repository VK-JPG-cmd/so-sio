import React from 'react';
import { motion } from 'framer-motion';
import { ThreatSeverity } from '../../types';
import { ShieldAlert, ShieldCheck, AlertTriangle, AlertOctagon } from 'lucide-react';

interface RiskGaugeProps {
  score: number; // 0 to 100
  severity?: ThreatSeverity;
  confidence?: number;
  modelVersion?: string;
  explanation?: string;
  size?: 'sm' | 'md' | 'lg';
  showDetails?: boolean;
  theme?: 'dark' | 'light';
}

export const RiskGauge: React.FC<RiskGaugeProps> = ({
  score,
  severity,
  confidence,
  modelVersion = 'RiskGuard-v4.2.1',
  explanation,
  size = 'md',
  showDetails = true,
  theme = 'dark',
}) => {
  const calculatedSeverity: ThreatSeverity = severity || (
    score >= 90 ? 'critical' :
    score >= 70 ? 'high' :
    score >= 40 ? 'medium' : 'low'
  );

  const severityConfig = {
    low: {
      color: '#2F7C5B',
      label: 'Low Risk',
      sublabel: 'Minimal anomaly detected',
      icon: ShieldCheck,
      badgeClass: 'bg-[#EAF5F0] text-[#2F7C5B] border-[#C3E4D6]',
    },
    medium: {
      color: '#B87B28',
      label: 'Medium Risk',
      sublabel: 'Requires analyst triage',
      icon: AlertTriangle,
      badgeClass: 'bg-[#FDF6E9] text-[#B87B28] border-[#F1DCBD]',
    },
    high: {
      color: '#C8485E',
      label: 'High Risk',
      sublabel: 'Active scam indicators',
      icon: ShieldAlert,
      badgeClass: 'bg-[#FDEEEF] text-[#C8485E] border-[#F5C4CB]',
    },
    critical: {
      color: '#FBF5A5',
      label: 'Critical Risk',
      sublabel: 'Immediate takedown recommended',
      icon: AlertOctagon,
      badgeClass: 'bg-[#111312] text-[#FBF5A5] border-[#434346] font-bold',
    },
  }[calculatedSeverity];

  const Icon = severityConfig.icon;

  const radius = size === 'sm' ? 36 : size === 'lg' ? 68 : 52;
  const strokeWidth = size === 'sm' ? 6 : size === 'lg' ? 10 : 8;
  const circumference = 2 * Math.PI * radius;
  const arcLength = circumference * 0.75;
  const strokeDashoffset = arcLength - (score / 100) * arcLength;

  const trackStroke = theme === 'dark' ? '#2B2D2C' : '#E2E1DC';
  const textColor = theme === 'dark' ? 'text-white' : 'text-[#111312]';
  const subtextColor = theme === 'dark' ? 'text-[#9A9B9C]' : 'text-[#737478]';
  const borderColor = theme === 'dark' ? 'border-[#2B2D2C]' : 'border-[#EAE9E4]';

  return (
    <div className="flex flex-col items-center">
      <div className="relative flex items-center justify-center">
        <svg
          className="transform -rotate-135"
          width={radius * 2 + strokeWidth * 2 + 16}
          height={radius * 2 + strokeWidth * 2 + 16}
        >
          {/* Background Track Arc */}
          <circle
            cx={radius + strokeWidth + 8}
            cy={radius + strokeWidth + 8}
            r={radius}
            fill="transparent"
            stroke={trackStroke}
            strokeWidth={strokeWidth}
            strokeDasharray={`${arcLength} ${circumference}`}
            strokeLinecap="round"
          />

          {/* Active Colored Arc */}
          <motion.circle
            cx={radius + strokeWidth + 8}
            cy={radius + strokeWidth + 8}
            r={radius}
            fill="transparent"
            stroke={severityConfig.color}
            strokeWidth={strokeWidth}
            strokeDasharray={`${arcLength} ${circumference}`}
            initial={{ strokeDashoffset: arcLength }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1.2, ease: "easeOut" }}
            strokeLinecap="round"
          />
        </svg>

        {/* Center Score Display */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className={`font-extrabold tracking-tight ${textColor} ${
            size === 'sm' ? 'text-lg' : size === 'lg' ? 'text-4xl' : 'text-2xl'
          }`}>
            {score}
          </span>
          <span className={`text-[10px] uppercase font-bold tracking-wider ${subtextColor}`}>
            / 100 Risk
          </span>
        </div>
      </div>

      {/* Severity Badge */}
      <div className="mt-2 flex items-center gap-1.5">
        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${severityConfig.badgeClass}`}>
          <Icon className="w-3.5 h-3.5 shrink-0" />
          <span>{severityConfig.label}</span>
        </span>
      </div>

      {showDetails && (
        <div className="mt-3 w-full text-center space-y-1.5">
          <p className={`text-xs ${subtextColor} leading-relaxed max-w-xs mx-auto`}>
            {explanation || severityConfig.sublabel}
          </p>

          <div className={`flex items-center justify-center gap-3 pt-2 text-[11px] ${subtextColor} border-t ${borderColor}`}>
            {confidence !== undefined && (
              <span className="inline-flex items-center gap-1">
                <span className={`font-semibold ${textColor}`}>Confidence:</span> {confidence}%
              </span>
            )}
            <span className="inline-flex items-center gap-1">
              <span className={`font-semibold ${textColor}`}>Engine:</span> {modelVersion}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
