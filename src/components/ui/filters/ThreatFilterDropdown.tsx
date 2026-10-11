import React, { useState, useRef, useEffect } from 'react';
import { Shield, ShieldAlert, Check, ChevronDown } from 'lucide-react';

export type ThreatFilterKey = 
  | 'all'
  // Severity options
  | 'critical'
  | 'high'
  | 'medium'
  | 'low'
  // Status options
  | 'active'
  | 'under_investigation'
  | 'takedown_requested'
  | 'resolved';

export interface ThreatFilterOptionItem {
  id: ThreatFilterKey;
  label: string;
  group: 'all' | 'severity' | 'status';
  dotColor?: string;
}

interface ThreatFilterDropdownProps {
  value: ThreatFilterKey;
  onChange: (value: ThreatFilterKey) => void;
  counts?: Partial<Record<ThreatFilterKey, number>>;
  align?: 'left' | 'right';
  className?: string;
}

const THREAT_OPTIONS: ThreatFilterOptionItem[] = [
  { id: 'all', label: 'All Threats', group: 'all' },
  // Risk levels
  { id: 'critical', label: 'Critical risk', group: 'severity', dotColor: 'bg-rose-500' },
  { id: 'high', label: 'High risk', group: 'severity', dotColor: 'bg-amber-500' },
  { id: 'medium', label: 'Medium risk', group: 'severity', dotColor: 'bg-yellow-400' },
  { id: 'low', label: 'Low risk', group: 'severity', dotColor: 'bg-emerald-500' },
  // Statuses
  { id: 'active', label: 'Active threats', group: 'status', dotColor: 'bg-rose-500' },
  { id: 'under_investigation', label: 'Being reviewed', group: 'status', dotColor: 'bg-sky-400' },
  { id: 'takedown_requested', label: 'Removal requested', group: 'status', dotColor: 'bg-purple-400' },
  { id: 'resolved', label: 'Resolved / Removed', group: 'status', dotColor: 'bg-emerald-400' },
];

export const ThreatFilterDropdown: React.FC<ThreatFilterDropdownProps> = ({
  value,
  onChange,
  counts = {},
  align = 'left',
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const currentOption = THREAT_OPTIONS.find((opt) => opt.id === value) || THREAT_OPTIONS[0];

  const handleSelect = (optionId: ThreatFilterKey) => {
    onChange(optionId);
    setIsOpen(false);
  };

  const severityOptions = THREAT_OPTIONS.filter((o) => o.group === 'severity');
  const statusOptions = THREAT_OPTIONS.filter((o) => o.group === 'status');

  return (
    <div className={`relative inline-block text-left ${className}`} ref={containerRef}>
      {/* Trigger Button - Matches clean UI in reference */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="true"
        aria-expanded={isOpen}
        className={`group flex items-center gap-2 px-3.5 py-2 rounded-2xl text-xs font-semibold tracking-wide transition-all duration-200 cursor-pointer select-none border ${
          isOpen
            ? 'bg-[#1C1F26] text-[#FBF5A5] border-[#2D313A] shadow-md'
            : value !== 'all'
            ? 'bg-[#1C1F26] text-white border-[#2D313A] shadow-xs'
            : 'bg-white text-[#111312] border-[#E2E1DC] hover:border-[#111312] hover:bg-[#FBFBF9] shadow-xs'
        }`}
      >
        <ShieldAlert
          className={`w-3.5 h-3.5 transition-colors ${
            isOpen || value !== 'all' ? 'text-[#FBF5A5]' : 'text-[#737478] group-hover:text-[#111312]'
          }`}
        />
        <div className="flex items-center gap-1.5">
          <span className="font-bold">
            {value === 'all' ? 'All Threats' : currentOption.label}
          </span>
          {counts[value] !== undefined && (
            <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded-full ${
              value !== 'all' || isOpen 
                ? 'bg-[#2D313A] text-[#FBF5A5]' 
                : 'bg-[#F4F3EF] text-[#737478]'
            }`}>
              {counts[value]}
            </span>
          )}
        </div>
        <ChevronDown
          className={`w-3.5 h-3.5 transition-transform duration-200 ${
            isOpen ? 'rotate-180 text-[#FBF5A5]' : 'text-[#737478] group-hover:text-[#111312]'
          }`}
        />
      </button>

      {/* Floating Dark Dropdown Panel */}
      {isOpen && (
        <div
          role="menu"
          aria-label="Threat filtering options"
          className={`absolute ${align === 'right' ? 'right-0' : 'left-0'} mt-2 w-72 max-w-[calc(100vw-32px)] z-50 rounded-3xl bg-[#1C1F26] border border-[#2D313A] shadow-2xl shadow-black/60 p-3 text-white transition-all transform origin-top animate-in fade-in zoom-in-95 duration-150 backdrop-blur-md max-h-[85vh] overflow-y-auto`}
        >
          {/* Header Label */}
          <div className="px-3 py-2 text-xs font-semibold text-[#8E929B] uppercase tracking-wider select-none">
            Filter Threats
          </div>

          {/* All Threats Option */}
          <button
            type="button"
            onClick={() => handleSelect('all')}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-sm font-medium transition-all duration-150 cursor-pointer select-none text-left mb-1 ${
              value === 'all'
                ? 'bg-[#262B35] text-white font-semibold'
                : 'text-[#E1E4EA] hover:bg-[#282C36] hover:text-white'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <span className="w-2 h-2 rounded-full bg-[#8E929B]" />
              <span>All Threats</span>
              {counts['all'] !== undefined && (
                <span className="text-[11px] text-[#8E929B]">({counts['all']})</span>
              )}
            </div>
            {value === 'all' && (
              <Check className="w-4 h-4 text-[#FBF5A5] stroke-[2.5] shrink-0" />
            )}
          </button>

          {/* Risk Level Group */}
          <div className="pt-2 mt-1 border-t border-[#2D313A]/70">
            <div className="px-3 py-1 text-[10px] font-bold text-[#8E929B] uppercase tracking-wider select-none">
              Risk Level
            </div>
            {severityOptions.map((opt) => {
              const isSelected = value === opt.id;
              const count = counts[opt.id];
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => handleSelect(opt.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-sm font-medium transition-all duration-150 cursor-pointer select-none text-left ${
                    isSelected
                      ? 'bg-[#262B35] text-white font-semibold'
                      : 'text-[#E1E4EA] hover:bg-[#282C36] hover:text-white'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <span className={`w-2 h-2 rounded-full shrink-0 ${opt.dotColor}`} />
                    <span>{opt.label}</span>
                    {count !== undefined && (
                      <span className="text-[11px] text-[#8E929B]">({count})</span>
                    )}
                  </div>
                  {isSelected && (
                    <Check className="w-4 h-4 text-[#FBF5A5] stroke-[2.5] shrink-0" />
                  )}
                </button>
              );
            })}
          </div>

          {/* Current Status Group */}
          <div className="pt-2 mt-1 border-t border-[#2D313A]/70">
            <div className="px-3 py-1 text-[10px] font-bold text-[#8E929B] uppercase tracking-wider select-none">
              Current Status
            </div>
            {statusOptions.map((opt) => {
              const isSelected = value === opt.id;
              const count = counts[opt.id];
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => handleSelect(opt.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-sm font-medium transition-all duration-150 cursor-pointer select-none text-left ${
                    isSelected
                      ? 'bg-[#262B35] text-white font-semibold'
                      : 'text-[#E1E4EA] hover:bg-[#282C36] hover:text-white'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <span className={`w-2 h-2 rounded-full shrink-0 ${opt.dotColor}`} />
                    <span>{opt.label}</span>
                    {count !== undefined && (
                      <span className="text-[11px] text-[#8E929B]">({count})</span>
                    )}
                  </div>
                  {isSelected && (
                    <Check className="w-4 h-4 text-[#FBF5A5] stroke-[2.5] shrink-0" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
