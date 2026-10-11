import React, { useState, useRef, useEffect } from 'react';
import { Calendar, Check, ChevronDown, ChevronRight, ArrowLeft } from 'lucide-react';

export type DateRangePreset = '7d' | '14d' | '30d' | '60d' | '90d' | 'custom';

export interface DateFilterValue {
  preset: DateRangePreset;
  label: string;
  startDate?: string; // YYYY-MM-DD
  endDate?: string;   // YYYY-MM-DD
}

interface DateFilterDropdownProps {
  value: DateFilterValue;
  onChange: (value: DateFilterValue) => void;
  align?: 'left' | 'right';
  className?: string;
}

const PRESETS: { id: DateRangePreset; label: string; days: number }[] = [
  { id: '7d', label: '7 days', days: 7 },
  { id: '14d', label: '14 days', days: 14 },
  { id: '30d', label: '30 days', days: 30 },
  { id: '60d', label: '60 days', days: 60 },
  { id: '90d', label: '90 days', days: 90 },
];

export const DateFilterDropdown: React.FC<DateFilterDropdownProps> = ({
  value,
  onChange,
  align = 'right',
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isCustomMode, setIsCustomMode] = useState(false);
  
  // Format today's date and default 30 days ago for custom inputs
  const todayStr = new Date().toISOString().split('T')[0];
  const thirtyDaysAgoStr = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  
  const [customStart, setCustomStart] = useState(value.startDate || thirtyDaysAgoStr);
  const [customEnd, setCustomEnd] = useState(value.endDate || todayStr);

  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside or escape key
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setIsCustomMode(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
        setIsCustomMode(false);
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

  const handleSelectPreset = (preset: typeof PRESETS[0]) => {
    onChange({
      preset: preset.id,
      label: preset.label,
    });
    setIsOpen(false);
    setIsCustomMode(false);
  };

  const handleApplyCustom = () => {
    if (!customStart || !customEnd) return;
    onChange({
      preset: 'custom',
      label: `${customStart.slice(5)} to ${customEnd.slice(5)}`,
      startDate: customStart,
      endDate: customEnd,
    });
    setIsOpen(false);
    setIsCustomMode(false);
  };

  return (
    <div className={`relative inline-block text-left ${className}`} ref={containerRef}>
      {/* Trigger Button - Matches clean UI in reference */}
      <button
        type="button"
        onClick={() => {
          setIsOpen(!isOpen);
          setIsCustomMode(false);
        }}
        aria-haspopup="true"
        aria-expanded={isOpen}
        className={`group flex items-center gap-2 px-3.5 py-2 rounded-2xl text-xs font-semibold tracking-wide transition-all duration-200 cursor-pointer select-none border ${
          isOpen
            ? 'bg-[#1C1F26] text-[#FBF5A5] border-[#2D313A] shadow-md'
            : 'bg-white text-[#111312] border-[#E2E1DC] hover:border-[#111312] hover:bg-[#FBFBF9] shadow-xs'
        }`}
      >
        <Calendar className={`w-3.5 h-3.5 transition-colors ${isOpen ? 'text-[#FBF5A5]' : 'text-[#737478] group-hover:text-[#111312]'}`} />
        <span className="font-bold">{value.label}</span>
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
          aria-label="Time period options"
          className={`absolute ${align === 'right' ? 'right-0' : 'left-0'} mt-2 w-72 max-w-[calc(100vw-32px)] z-50 rounded-3xl bg-[#1C1F26] border border-[#2D313A] shadow-2xl shadow-black/60 p-3 text-white transition-all transform origin-top animate-in fade-in zoom-in-95 duration-150 backdrop-blur-md`}
        >
          {!isCustomMode ? (
            <div className="space-y-1">
              {/* Header Label - Matches "Time period" in Reference Screenshot */}
              <div className="px-3 py-2 text-xs font-semibold text-[#8E929B] uppercase tracking-wider select-none">
                Time period
              </div>

              {/* Presets List */}
              {PRESETS.map((p) => {
                const isSelected = value.preset === p.id;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => handleSelectPreset(p)}
                    className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-sm font-medium transition-all duration-150 cursor-pointer select-none text-left ${
                      isSelected
                        ? 'bg-[#262B35] text-white font-semibold'
                        : 'text-[#E1E4EA] hover:bg-[#282C36] hover:text-white'
                    }`}
                  >
                    <span>{p.label}</span>
                    {isSelected && (
                      <Check className="w-4 h-4 text-[#FBF5A5] stroke-[2.5] shrink-0" />
                    )}
                  </button>
                );
              })}

              {/* Custom Range Trigger */}
              <div className="pt-1 mt-1 border-t border-[#2D313A]">
                <button
                  type="button"
                  onClick={() => setIsCustomMode(true)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-sm font-medium transition-all duration-150 cursor-pointer select-none text-left ${
                    value.preset === 'custom'
                      ? 'bg-[#262B35] text-white font-semibold'
                      : 'text-[#E1E4EA] hover:bg-[#282C36] hover:text-white'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    Custom range
                    {value.preset === 'custom' && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-[#FBF5A5]/20 text-[#FBF5A5] border border-[#FBF5A5]/30">
                        Active
                      </span>
                    )}
                  </span>
                  <ChevronRight className="w-4 h-4 text-[#8E929B] shrink-0" />
                </button>
              </div>
            </div>
          ) : (
            /* Custom Date Range Picker View */
            <div className="p-1 space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold text-[#8E929B] pb-1 border-b border-[#2D313A]">
                <button
                  type="button"
                  onClick={() => setIsCustomMode(false)}
                  className="p-1 rounded-lg hover:bg-[#282C36] text-white transition-colors cursor-pointer"
                  title="Back to presets"
                >
                  <ArrowLeft className="w-4 h-4" />
                </button>
                <span className="uppercase tracking-wider">Select Custom Dates</span>
              </div>

              <div className="space-y-2.5">
                <div>
                  <label className="block text-[11px] font-medium text-[#A0A4AD] mb-1">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={customStart}
                    onChange={(e) => setCustomStart(e.target.value)}
                    max={customEnd || todayStr}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-[#262B35] border border-[#3A404D] text-white focus:outline-none focus:border-[#FBF5A5] focus:ring-1 focus:ring-[#FBF5A5] transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-[#A0A4AD] mb-1">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={customEnd}
                    onChange={(e) => setCustomEnd(e.target.value)}
                    min={customStart}
                    max={todayStr}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-[#262B35] border border-[#3A404D] text-white focus:outline-none focus:border-[#FBF5A5] focus:ring-1 focus:ring-[#FBF5A5] transition-colors"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2 border-t border-[#2D313A]">
                <button
                  type="button"
                  onClick={() => setIsCustomMode(false)}
                  className="flex-1 py-2 rounded-xl text-xs font-medium text-[#A0A4AD] hover:bg-[#282C36] hover:text-white transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleApplyCustom}
                  className="flex-1 py-2 rounded-xl text-xs font-bold bg-[#FBF5A5] text-[#111312] hover:bg-[#F3EB7D] transition-colors shadow-sm cursor-pointer"
                >
                  Apply Range
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
