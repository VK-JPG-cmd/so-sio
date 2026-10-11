import React, { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useBrand } from '../../context/BrandContext';
import { threatService, reportService } from '../../services/api';
import { SuspiciousThreat, CustomerReport } from '../../types';
import { Card } from '../../components/ui/Card';
import { StatCard } from '../../components/ui/StatCard';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { RiskGauge } from '../../components/ui/RiskGauge';
import { 
  ShieldAlert, 
  Globe2, 
  Users2, 
  Search, 
  ArrowRight, 
  AlertTriangle, 
  CheckCircle2, 
  TrendingUp, 
  Sparkles, 
  ExternalLink,
  ShieldCheck,
  Send,
  FileText,
  AlertOctagon,
  Lightbulb,
  Crosshair,
  Shield,
  RotateCcw,
  SlidersHorizontal
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';
import { 
  DateFilterDropdown, 
  DateFilterValue, 
  ThreatFilterDropdown, 
  ThreatFilterKey 
} from '../../components/ui/filters';

import { DemoWorkflow } from '../demo/DemoWorkflow';

export const OverviewDashboard: React.FC = () => {
  const { currentBrand } = useBrand();
  const [threats, setThreats] = useState<SuspiciousThreat[]>([]);
  const [reports, setReports] = useState<CustomerReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showDemoPipeline, setShowDemoPipeline] = useState(false);
  const navigate = useNavigate();

  // Reference-styled filter states
  const [dateFilter, setDateFilter] = useState<DateFilterValue>({
    preset: '30d',
    label: '30 days'
  });
  const [threatFilter, setThreatFilter] = useState<ThreatFilterKey>('all');

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      try {
        const [threatList, reportList] = await Promise.all([
          threatService.getThreats(currentBrand?.id),
          reportService.getReports(undefined, currentBrand?.id)
        ]);
        setThreats(threatList);
        setReports(reportList);
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, [currentBrand]);

  // Use October 10, 2026 as reference anchor so our mock dates match today's simulated timeframe
  const anchorTimestamp = useMemo(() => {
    return new Date('2026-10-10T23:59:59Z').getTime();
  }, []);

  // Filtered threats based on both Date Filter and Threat Filter
  const filteredThreats = useMemo(() => {
    return threats.filter((t) => {
      // 1. Date Range Filter
      const threatTime = new Date(t.firstSeenAt).getTime();
      if (dateFilter.preset === 'custom' && dateFilter.startDate && dateFilter.endDate) {
        const start = new Date(`${dateFilter.startDate}T00:00:00Z`).getTime();
        const end = new Date(`${dateFilter.endDate}T23:59:59Z`).getTime();
        if (threatTime < start || threatTime > end) return false;
      } else {
        const days = 
          dateFilter.preset === '7d' ? 7 :
          dateFilter.preset === '14d' ? 14 :
          dateFilter.preset === '30d' ? 30 :
          dateFilter.preset === '60d' ? 60 :
          dateFilter.preset === '90d' ? 90 : 30;
        const cutoff = anchorTimestamp - (days * 24 * 60 * 60 * 1000);
        if (threatTime < cutoff) return false;
      }

      // 2. Threat Filter (Severity or Status)
      if (threatFilter === 'all') return true;
      if (['critical', 'high', 'medium', 'low'].includes(threatFilter)) {
        return t.severity === threatFilter;
      }
      if (['active', 'under_investigation', 'takedown_requested', 'resolved'].includes(threatFilter)) {
        return t.status === threatFilter;
      }
      return true;
    });
  }, [threats, dateFilter, threatFilter, anchorTimestamp]);

  // Compute live threat counts by filter option for the dropdown badges
  const threatFilterCounts = useMemo(() => {
    const inDateThreats = threats.filter((t) => {
      const threatTime = new Date(t.firstSeenAt).getTime();
      if (dateFilter.preset === 'custom' && dateFilter.startDate && dateFilter.endDate) {
        const start = new Date(`${dateFilter.startDate}T00:00:00Z`).getTime();
        const end = new Date(`${dateFilter.endDate}T23:59:59Z`).getTime();
        return threatTime >= start && threatTime <= end;
      }
      const days = 
        dateFilter.preset === '7d' ? 7 :
        dateFilter.preset === '14d' ? 14 :
        dateFilter.preset === '30d' ? 30 :
        dateFilter.preset === '60d' ? 60 :
        dateFilter.preset === '90d' ? 90 : 30;
      return threatTime >= (anchorTimestamp - days * 24 * 60 * 60 * 1000);
    });

    return {
      all: inDateThreats.length,
      critical: inDateThreats.filter(t => t.severity === 'critical').length,
      high: inDateThreats.filter(t => t.severity === 'high').length,
      medium: inDateThreats.filter(t => t.severity === 'medium').length,
      low: inDateThreats.filter(t => t.severity === 'low').length,
      active: inDateThreats.filter(t => t.status === 'active').length,
      under_investigation: inDateThreats.filter(t => t.status === 'under_investigation').length,
      takedown_requested: inDateThreats.filter(t => t.status === 'takedown_requested').length,
      resolved: inDateThreats.filter(t => t.status === 'resolved').length,
    };
  }, [threats, dateFilter, anchorTimestamp]);

  // Dynamic Chart data for Threat Activity Trend adapting to selected timeframe & threat filter
  const activityTrendData = useMemo(() => {
    const countMultiplier = 
      threatFilter === 'critical' ? 0.35 :
      threatFilter === 'high' ? 0.45 :
      threatFilter === 'medium' ? 0.25 :
      threatFilter === 'low' ? 0.15 :
      threatFilter === 'resolved' ? 0.5 : 1;

    if (dateFilter.preset === '7d') {
      return [
        { day: 'Oct 4', threats: Math.max(1, Math.round(12 * countMultiplier)), blocked: Math.round(10 * countMultiplier) },
        { day: 'Oct 5', threats: Math.max(1, Math.round(19 * countMultiplier)), blocked: Math.round(16 * countMultiplier) },
        { day: 'Oct 6', threats: Math.max(1, Math.round(15 * countMultiplier)), blocked: Math.round(14 * countMultiplier) },
        { day: 'Oct 7', threats: Math.max(2, Math.round(28 * countMultiplier)), blocked: Math.round(24 * countMultiplier) },
        { day: 'Oct 8', threats: Math.max(2, Math.round(34 * countMultiplier)), blocked: Math.round(31 * countMultiplier) },
        { day: 'Oct 9', threats: Math.max(1, Math.round(22 * countMultiplier)), blocked: Math.round(20 * countMultiplier) },
        { day: 'Oct 10', threats: Math.max(1, Math.round(18 * countMultiplier)), blocked: Math.round(18 * countMultiplier) },
      ];
    } else if (dateFilter.preset === '14d') {
      return [
        { day: 'Sep 27', threats: Math.max(1, Math.round(14 * countMultiplier)), blocked: Math.round(12 * countMultiplier) },
        { day: 'Sep 29', threats: Math.max(2, Math.round(22 * countMultiplier)), blocked: Math.round(18 * countMultiplier) },
        { day: 'Oct 1', threats: Math.max(2, Math.round(26 * countMultiplier)), blocked: Math.round(24 * countMultiplier) },
        { day: 'Oct 3', threats: Math.max(3, Math.round(31 * countMultiplier)), blocked: Math.round(28 * countMultiplier) },
        { day: 'Oct 5', threats: Math.max(3, Math.round(38 * countMultiplier)), blocked: Math.round(34 * countMultiplier) },
        { day: 'Oct 7', threats: Math.max(2, Math.round(29 * countMultiplier)), blocked: Math.round(27 * countMultiplier) },
        { day: 'Oct 10', threats: Math.max(1, Math.round(20 * countMultiplier)), blocked: Math.round(19 * countMultiplier) },
      ];
    } else if (dateFilter.preset === '60d') {
      return [
        { day: 'Aug 15', threats: Math.max(2, Math.round(45 * countMultiplier)), blocked: Math.round(40 * countMultiplier) },
        { day: 'Aug 30', threats: Math.max(3, Math.round(62 * countMultiplier)), blocked: Math.round(55 * countMultiplier) },
        { day: 'Sep 10', threats: Math.max(4, Math.round(78 * countMultiplier)), blocked: Math.round(70 * countMultiplier) },
        { day: 'Sep 20', threats: Math.max(5, Math.round(89 * countMultiplier)), blocked: Math.round(82 * countMultiplier) },
        { day: 'Sep 30', threats: Math.max(4, Math.round(96 * countMultiplier)), blocked: Math.round(90 * countMultiplier) },
        { day: 'Oct 10', threats: Math.max(3, Math.round(84 * countMultiplier)), blocked: Math.round(80 * countMultiplier) },
      ];
    } else if (dateFilter.preset === '90d') {
      return [
        { day: 'Jul', threats: Math.max(4, Math.round(75 * countMultiplier)), blocked: Math.round(68 * countMultiplier) },
        { day: 'Aug', threats: Math.max(5, Math.round(110 * countMultiplier)), blocked: Math.round(102 * countMultiplier) },
        { day: 'Sep', threats: Math.max(6, Math.round(145 * countMultiplier)), blocked: Math.round(136 * countMultiplier) },
        { day: 'Oct', threats: Math.max(5, Math.round(128 * countMultiplier)), blocked: Math.round(122 * countMultiplier) },
      ];
    } else {
      // 30d default or custom
      return [
        { day: 'Sep 10', threats: Math.max(1, Math.round(12 * countMultiplier)), blocked: Math.round(10 * countMultiplier) },
        { day: 'Sep 15', threats: Math.max(1, Math.round(19 * countMultiplier)), blocked: Math.round(16 * countMultiplier) },
        { day: 'Sep 20', threats: Math.max(2, Math.round(25 * countMultiplier)), blocked: Math.round(21 * countMultiplier) },
        { day: 'Sep 25', threats: Math.max(2, Math.round(31 * countMultiplier)), blocked: Math.round(27 * countMultiplier) },
        { day: 'Sep 30', threats: Math.max(3, Math.round(38 * countMultiplier)), blocked: Math.round(34 * countMultiplier) },
        { day: 'Oct 5', threats: Math.max(2, Math.round(30 * countMultiplier)), blocked: Math.round(28 * countMultiplier) },
        { day: 'Oct 10', threats: Math.max(1, Math.round(22 * countMultiplier)), blocked: Math.round(21 * countMultiplier) },
      ];
    }
  }, [dateFilter.preset, threatFilter]);

  // Dynamic Category Distribution from filtered threats
  const categoryData = useMemo(() => {
    if (filteredThreats.length > 0) {
      const counts: Record<string, number> = {};
      filteredThreats.forEach(t => {
        let label = 'Fake websites';
        if (t.category.includes('typo')) label = 'Lookalike websites';
        else if (t.category.includes('social') || t.category.includes('exec')) label = 'Fake social accounts';
        else if (t.category.includes('mobile')) label = 'Fake mobile apps';
        else if (t.category.includes('credential')) label = 'Password theft sites';
        counts[label] = (counts[label] || 0) + 1;
      });

      const total = filteredThreats.length;
      const palette: Record<string, string> = {
        'Fake websites': '#C8485E',
        'Lookalike websites': '#B87B28',
        'Fake social accounts': '#434346',
        'Fake mobile apps': '#111312',
        'Password theft sites': '#7C3AED',
      };

      return Object.entries(counts).map(([name, count]) => ({
        name,
        value: Math.round((count / total) * 100),
        color: palette[name] || '#64748B'
      }));
    }

    return [
      { name: 'Fake websites', value: 45, color: '#C8485E' },
      { name: 'Lookalike websites', value: 28, color: '#B87B28' },
      { name: 'Fake social accounts', value: 18, color: '#434346' },
      { name: 'Fake mobile apps', value: 9, color: '#111312' },
    ];
  }, [filteredThreats]);

  // Dynamic KPI metrics updated by filtered threats
  const activeThreatsCount = useMemo(() => {
    return filteredThreats.filter(t => t.status === 'active' || t.status === 'under_investigation').length;
  }, [filteredThreats]);

  const activeCampaignsCount = useMemo(() => {
    if (threatFilter === 'resolved' || threatFilter === 'low') return 0;
    return filteredThreats.some(t => t.campaignId) ? 1 : 0;
  }, [filteredThreats, threatFilter]);

  const criticalThreatsCount = useMemo(() => {
    return filteredThreats.filter(t => t.severity === 'critical').length;
  }, [filteredThreats]);

  const threatsRemovedCount = useMemo(() => {
    const resolvedInFilter = filteredThreats.filter(t => t.status === 'resolved').length;
    // Scale baseline by time window
    const baseWindow = 
      dateFilter.preset === '7d' ? 24 :
      dateFilter.preset === '14d' ? 52 :
      dateFilter.preset === '30d' ? 138 :
      dateFilter.preset === '60d' ? 210 :
      dateFilter.preset === '90d' ? 284 : 138;
    return baseWindow + resolvedInFilter;
  }, [filteredThreats, dateFilter.preset]);

  // Dynamic Digital Risk Score and Level derived from filtered threats data
  const riskScore = useMemo(() => {
    if (filteredThreats.length > 0) {
      const active = filteredThreats.filter(t => t.status === 'active' || t.status === 'under_investigation');
      if (active.length > 0) {
        const avg = Math.round(active.reduce((acc, t) => acc + (t.riskScore || 80), 0) / active.length);
        return Math.min(100, Math.max(45, avg));
      }
      const avg = Math.round(filteredThreats.reduce((acc, t) => acc + (t.riskScore || 60), 0) / filteredThreats.length);
      return Math.max(30, avg - 25);
    }
    return 35; // Safe baseline when 0 matching threats
  }, [filteredThreats]);

  const riskLevel = useMemo(() => {
    if (riskScore >= 75) {
      return {
        label: 'High Risk',
        color: '#C8485E',
        bgColor: 'bg-[#FDEEEF]',
        textColor: 'text-[#C8485E]',
        borderColor: 'border-[#F5C4CB]',
      };
    }
    if (riskScore >= 45) {
      return {
        label: 'Medium Risk',
        color: '#B87B28',
        bgColor: 'bg-[#FDF6E9]',
        textColor: 'text-[#B87B28]',
        borderColor: 'border-[#F1DCBD]',
      };
    }
    return {
      label: 'Low Risk',
      color: '#2F7C5B',
      bgColor: 'bg-[#EAF5F0]',
      textColor: 'text-[#2F7C5B]',
      borderColor: 'border-[#C3E4D6]',
    };
  }, [riskScore]);

  // Threats needing immediate attention filtered reactively
  const urgentThreats = useMemo(() => {
    if (threatFilter === 'all') {
      return filteredThreats.filter(t => t.severity === 'critical' || t.status === 'active').slice(0, 4);
    }
    return filteredThreats.slice(0, 4);
  }, [filteredThreats, threatFilter]);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">

      {/* Interactive Evaluation Walkthrough Modal / Banner */}
      <div className="flex items-center justify-between bg-stone-900 text-white px-5 py-3.5 rounded-2xl shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-stone-200">
              Evaluator Interactive Walkthrough
            </h3>
            <p className="text-xs text-stone-400">
              Test live brand onboarding, lookalike domains, social impersonation, and dangerous APK analysis.
            </p>
          </div>
        </div>
        <button
          onClick={() => setShowDemoPipeline(!showDemoPipeline)}
          className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-stone-950 font-bold text-xs rounded-xl transition-all shadow-sm active:scale-95 flex items-center gap-1.5"
        >
          {showDemoPipeline ? 'Hide Walkthrough' : 'Launch Interactive Demo'}
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {showDemoPipeline && (
        <div className="animate-in fade-in slide-in-from-top-4 duration-300">
          <DemoWorkflow />
        </div>
      )}
      
      {/* Refined Brand Profile Header Banner */}
      <div className="bg-white p-5 sm:p-6 rounded-3xl border border-[#E2E1DC] shadow-sm space-y-4">
        {/* Main Balanced Top Row: Brand Profile (Left) & Circular Risk Score + Actions (Right) */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5">
          {/* Left Section: Circular Logo, Name, Verification Symbol, Category, and Description */}
          <div className="flex items-center gap-4 min-w-0">
            <img
              src={currentBrand?.logoUrl || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=120&auto=format&fit=crop&q=80'}
              alt={currentBrand?.name || 'Brand Logo'}
              className="w-14 h-14 sm:w-16 sm:h-16 rounded-full object-cover border-2 border-[#E2E1DC] shadow-xs shrink-0"
            />
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <div className="flex items-center gap-1.5 min-w-0">
                  <h1 className="text-xl sm:text-2xl font-extrabold text-[#111312] tracking-tight truncate">
                    {currentBrand?.name || 'ApexBank Global'}
                  </h1>
                  {(currentBrand?.verificationStatus === 'verified' || !currentBrand?.verificationStatus) && (
                    <span
                      tabIndex={0}
                      role="img"
                      title="Verified Official"
                      aria-label="Verified Official"
                      className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-[#FBF5A5] text-[#111312] border border-[#EBE47A] shadow-2xs shrink-0 cursor-default hover:scale-105 focus:outline-hidden focus:ring-2 focus:ring-[#111312] transition-transform"
                    >
                      <ShieldCheck className="w-3.5 h-3.5 fill-[#111312] text-[#FBF5A5]" />
                    </span>
                  )}
                </div>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#F4F3EF] text-[#111312] font-bold border border-[#DCDAD4] shrink-0">
                  {currentBrand?.industry || 'Banking & Fintech'}
                </span>
              </div>
              <p className="text-xs text-[#737478] mt-1 max-w-xl leading-relaxed">
                Official Digital Perimeter active across 450+ domain registrars, social networks, and mobile app ecosystems.
              </p>
            </div>
          </div>

          {/* Right Section: Compact Circular Digital Risk Score & Existing Action Buttons */}
          <div className="flex flex-wrap items-center gap-4 sm:gap-6 shrink-0 self-start lg:self-center">
            {/* Compact Circular Digital Risk Score Indicator */}
            <div 
              className="flex items-center gap-3 bg-[#FBFBF9] p-2 pl-2.5 pr-3.5 rounded-2xl border border-[#EAE9E4]"
              title={`Digital Risk Score: ${riskScore}/100 (${riskLevel.label})`}
            >
              <div className="relative w-12 h-12 flex items-center justify-center shrink-0">
                <svg className="w-12 h-12 -rotate-90 transform" viewBox="0 0 48 48" aria-hidden="true">
                  <circle
                    cx="24"
                    cy="24"
                    r="19"
                    className="stroke-[#EAE9E4]"
                    strokeWidth="3.5"
                    fill="transparent"
                  />
                  <circle
                    cx="24"
                    cy="24"
                    r="19"
                    stroke={riskLevel.color}
                    strokeWidth="3.5"
                    fill="transparent"
                    strokeDasharray={119.38}
                    strokeDashoffset={119.38 - (119.38 * Math.min(riskScore, 100)) / 100}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                  <span className="text-sm font-extrabold text-[#111312] leading-none">
                    {riskScore}
                  </span>
                  <span className="text-[7px] font-bold tracking-wider text-[#737478] uppercase mt-0.5">
                    RISK
                  </span>
                </div>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] font-bold text-[#737478] uppercase tracking-wider">
                  Risk Level
                </span>
                <span className={`text-[11px] font-extrabold px-2.5 py-0.5 rounded-full border mt-0.5 text-center ${riskLevel.bgColor} ${riskLevel.textColor} ${riskLevel.borderColor}`}>
                  Risk level: {riskLevel.label.replace(' Risk', '')}
                </span>
                <span className="sr-only">
                  Risk level: {riskLevel.label}, Score: {riskScore} out of 100
                </span>
              </div>
            </div>

            {/* Existing Action Buttons */}
            <div className="flex items-center gap-2.5">
              <Link to="/brand-owner/reports">
                <Button variant="outline" size="sm" leftIcon={<FileText className="w-4 h-4" />}>
                  Export Risk Brief
                </Button>
              </Link>
              <Link to="/brand-owner/threat-management">
                <Button size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                  Threat Workspace
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Compact Executive Business Insight Strip Below Main Header */}
        <div className="pt-3 border-t border-[#EAE9E4] flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-lg bg-[#111312] text-[#FBF5A5] flex items-center justify-center shrink-0 shadow-2xs">
            <Lightbulb className="w-3.5 h-3.5" />
          </div>
          <p className="text-xs text-[#737478] leading-relaxed">
            <strong className="text-[#111312] font-bold mr-1.5">Executive Insight:</strong>
            <strong className="text-[#111312]">{activeCampaignsCount} active fake campaign{activeCampaignsCount === 1 ? '' : 's'}</strong> targeting customers.&nbsp;
            <strong className="text-emerald-700 font-semibold">{threatsRemovedCount} fake sites & accounts</strong> taken down.&nbsp;
            Immediate action recommended for <strong className="text-[#C8485E] font-semibold">{criticalThreatsCount} critical fake site{criticalThreatsCount === 1 ? '' : 's'}</strong>.
          </p>
        </div>
      </div>

      {/* Modern Filter Control Bar (Matching Reference Screenshot) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3.5 px-5 py-3.5 rounded-3xl bg-white border border-[#E2E1DC] shadow-xs">
        {/* Left: Section Scope Title & Live Count */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#111312]" />
            <h2 className="text-xs font-bold text-[#111312] uppercase tracking-wider">
              Threats Found & Activity
            </h2>
          </div>
          <span className="text-xs text-[#737478]">
            <strong className="text-[#111312] font-bold">{filteredThreats.length}</strong> threat{filteredThreats.length === 1 ? '' : 's'} found
          </span>
          {(threatFilter !== 'all' || dateFilter.preset !== '30d') && (
            <button
              type="button"
              onClick={() => {
                setThreatFilter('all');
                setDateFilter({ preset: '30d', label: '30 days' });
              }}
              className="inline-flex items-center gap-1 text-[11px] font-bold text-[#737478] hover:text-[#111312] transition-colors cursor-pointer ml-1"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset filters</span>
            </button>
          )}
        </div>

        {/* Right: Dark Rounded Dropdowns from Reference Screenshot */}
        <div className="flex items-center gap-2.5 flex-wrap self-end sm:self-auto">
          {/* Threat Filter Dropdown */}
          <ThreatFilterDropdown
            value={threatFilter}
            onChange={setThreatFilter}
            counts={threatFilterCounts}
            align="right"
          />

          {/* Date Filter Dropdown */}
          <DateFilterDropdown
            value={dateFilter}
            onChange={setDateFilter}
            align="right"
          />
        </div>
      </div>

      {/* 4 Core Required Dashboard Counters */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        
        <StatCard
          title="Active Threats"
          value={activeThreatsCount}
          icon={ShieldAlert}
          accentColor="rose"
          subtitle="Under active triage & tracking"
          change={{ value: '-3', trend: 'down', label: 'vs last 24h' }}
          onClick={() => navigate('/brand-owner/threat-management')}
        />

        <StatCard
          title="Active Scam Campaigns"
          value={activeCampaignsCount}
          icon={Crosshair}
          accentColor="purple"
          subtitle="Coordinated fraud syndicates"
          change={{ value: 'Stable', trend: 'neutral', label: 'past 7 days' }}
          onClick={() => navigate('/brand-owner/campaign-overview')}
        />

        <StatCard
          title="Critical Threats"
          value={criticalThreatsCount}
          icon={AlertOctagon}
          accentColor="amber"
          subtitle="Requires immediate attention"
          change={{ value: '2 urgent', trend: 'up', label: 'high priority' }}
          onClick={() => navigate('/brand-owner/threat-management?severity=critical')}
        />

        <StatCard
          title="Threats Removed"
          value={threatsRemovedCount}
          icon={CheckCircle2}
          accentColor="emerald"
          subtitle="Registrar takedowns executed"
          change={{ value: '98%', trend: 'up', label: 'resolution rate' }}
          onClick={() => navigate('/brand-owner/threat-management?status=resolved')}
        />

      </div>

      {/* PROMINENT SECTION: Threats That Need Immediate Attention */}
      <Card
        header={
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-rose-500 animate-ping" />
              <div>
                <h3 className="text-sm font-bold text-brand-dark">Threats Needing Immediate Attention</h3>
                <p className="text-xs text-brand-muted">Dangerous fake sites or accounts trying to trick your customers right now</p>
              </div>
            </div>
            <Link to="/brand-owner/threat-management" className="text-xs font-bold text-[#111312] hover:underline flex items-center gap-1">
              <span>View All Threats</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        }
        className="border-rose-200/80 shadow-soft"
      >
        <div className="space-y-3">
          {urgentThreats.length > 0 ? (
            urgentThreats.map((threat) => (
              <div 
                key={threat.id} 
                className="p-4 rounded-2xl bg-rose-50/40 hover:bg-rose-50/70 border border-rose-100 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono font-bold text-brand-dark text-sm">
                      {threat.targetDomainOrUrl}
                    </span>
                    <Badge severity={threat.severity} size="sm" />
                    <Badge status={threat.status} size="sm" />
                  </div>
                  <p className="text-xs text-brand-muted leading-relaxed">
                    {threat.riskExplanation}
                  </p>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Link to={`/brand-owner/threats/${threat.id}`}>
                    <Button variant="secondary" size="sm">
                      Investigate
                    </Button>
                  </Link>
                  <Link to={`/brand-owner/recommended-actions?threatId=${threat.id}`}>
                    <Button size="sm" leftIcon={<Send className="w-3.5 h-3.5" />}>
                      Take Action
                    </Button>
                  </Link>
                </div>
              </div>
            ))
          ) : (
            <div className="p-8 rounded-2xl bg-[#FBFBF9] border border-[#EAE9E4] text-center space-y-2">
              <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
              <p className="text-sm font-bold text-[#111312]">No immediate threats matching this filter scope</p>
              <p className="text-xs text-[#737478]">
                All assets within {dateFilter.label} match healthy security baseline parameters.
              </p>
              <button
                type="button"
                onClick={() => {
                  setThreatFilter('all');
                  setDateFilter({ preset: '30d', label: '30 days' });
                }}
                className="mt-2 text-xs font-bold text-[#111312] underline hover:text-black cursor-pointer"
              >
                Reset to All Threats (30 days)
              </button>
            </div>
          )}
        </div>
      </Card>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Threat Activity Over Time (7-Column) */}
        <div className="lg:col-span-8">
          <Card
            header={
              <div className="flex items-center justify-between w-full">
                <div>
                  <h3 className="text-sm font-bold text-brand-dark">Threats Detected & Removed Over Time</h3>
                  <p className="text-xs text-brand-muted">Live updates across automated internet scanning and verified customer reports</p>
                </div>
                <div className="flex items-center gap-4 text-xs font-semibold">
                  <span className="flex items-center gap-1.5 text-[#111312]">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#111312]" /> Threats found
                  </span>
                  <span className="flex items-center gap-1.5 text-emerald-700">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#2F7C5B]" /> Taken down
                  </span>
                </div>
              </div>
            }
          >
            <div className="h-72 w-full pt-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={activityTrendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="threatGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#111312" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#111312" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="blockGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2F7C5B" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#2F7C5B" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="day" stroke="#777083" fontSize={11} tickLine={false} />
                  <YAxis stroke="#777083" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      borderRadius: '16px',
                      border: '1px solid #E2E1DC',
                      boxShadow: '0 10px 25px rgba(17, 19, 18, 0.08)',
                      fontSize: '12px'
                    }}
                  />
                  <Area type="monotone" dataKey="threats" stroke="#111312" strokeWidth={2.5} fillOpacity={1} fill="url(#threatGrad)" />
                  <Area type="monotone" dataKey="blocked" stroke="#2F7C5B" strokeWidth={2.5} fillOpacity={1} fill="url(#blockGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        {/* Threat Category Breakdown (4-Column) */}
        <div className="lg:col-span-4">
          <Card
            header={
              <div>
                <h3 className="text-sm font-bold text-brand-dark">Types of Threats Found</h3>
                <p className="text-xs text-brand-muted">Breakdown of lookalike websites, fake accounts, and apps</p>
              </div>
            }
          >
            <div className="h-52 w-full flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {categoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="space-y-2 pt-2 border-t border-brand-border/50 text-xs">
              {categoryData.map((cat) => (
                <div key={cat.name} className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-brand-muted">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cat.color }} />
                    <span>{cat.name}</span>
                  </span>
                  <span className="font-bold text-brand-dark">{cat.value}%</span>
                </div>
              ))}
            </div>
          </Card>
        </div>

      </div>

    </div>
  );
};
