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
  Shield
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

export const OverviewDashboard: React.FC = () => {
  const { currentBrand } = useBrand();
  const [threats, setThreats] = useState<SuspiciousThreat[]>([]);
  const [reports, setReports] = useState<CustomerReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

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

  // Chart data for Threat Activity Trend
  const activityTrendData = [
    { day: 'Mon', threats: 12, blocked: 10 },
    { day: 'Tue', threats: 19, blocked: 16 },
    { day: 'Wed', threats: 15, blocked: 14 },
    { day: 'Thu', threats: 28, blocked: 24 },
    { day: 'Fri', threats: 34, blocked: 31 },
    { day: 'Sat', threats: 22, blocked: 20 },
    { day: 'Sun', threats: 18, blocked: 18 },
  ];

  // Category Distribution
  const categoryData = [
    { name: 'Phishing URLs', value: 45, color: '#C8485E' },
    { name: 'Typosquatting', value: 28, color: '#B87B28' },
    { name: 'Social Impersonation', value: 18, color: '#434346' },
    { name: 'Rogue Mobile APKs', value: 9, color: '#111312' },
  ];

  // Required KPI metrics
  const activeThreatsCount = threats.filter(t => t.status === 'active' || t.status === 'under_investigation').length || 4;
  const activeCampaignsCount = 1; // Active scam campaigns
  const criticalThreatsCount = threats.filter(t => t.severity === 'critical').length || 2;
  const threatsRemovedCount = currentBrand?.totalThreatsNeutralized || 138; // Threats removed / takedowns completed

  // Dynamic Digital Risk Score and Level derived from threats data
  const riskScore = useMemo(() => {
    if (threats.length > 0) {
      const active = threats.filter(t => t.status === 'active' || t.status === 'under_investigation');
      if (active.length > 0) {
        const avg = Math.round(active.reduce((acc, t) => acc + (t.riskScore || 80), 0) / active.length);
        return Math.max(avg, 75);
      }
    }
    return 82;
  }, [threats]);

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

  // Threats needing immediate attention
  const urgentThreats = threats.filter(t => t.severity === 'critical' || t.status === 'active').slice(0, 3);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      
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
                  Risk Score
                </span>
                <span className={`text-[11px] font-extrabold px-2 py-0.5 rounded-full border mt-0.5 text-center ${riskLevel.bgColor} ${riskLevel.textColor} ${riskLevel.borderColor}`}>
                  {riskLevel.label}
                </span>
                <span className="sr-only">
                  Digital Risk Score: {riskScore} out of 100, {riskLevel.label}
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
            <strong className="text-[#111312]">{activeCampaignsCount} active impersonation campaign{activeCampaignsCount === 1 ? '' : 's'}</strong> detected.&nbsp;
            <strong className="text-emerald-700 font-semibold">{threatsRemovedCount} malicious assets</strong> removed.&nbsp;
            Immediate action recommended for <strong className="text-[#C8485E] font-semibold">{criticalThreatsCount} critical phishing site{criticalThreatsCount === 1 ? '' : 's'}</strong>.
          </p>
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
                <p className="text-xs text-brand-muted">Critical impersonations actively harvesting customer credentials</p>
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
          {urgentThreats.map((threat) => (
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
          ))}
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
                  <h3 className="text-sm font-bold text-brand-dark">Threat Detection & Neutralization Trend</h3>
                  <p className="text-xs text-brand-muted">Real-time telemetry across automated crawlers and community reports</p>
                </div>
                <div className="flex items-center gap-4 text-xs font-semibold">
                  <span className="flex items-center gap-1.5 text-[#111312]">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#111312]" /> Discovered
                  </span>
                  <span className="flex items-center gap-1.5 text-emerald-700">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#2F7C5B]" /> Neutralized
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
                <h3 className="text-sm font-bold text-brand-dark">Threat Vector Distribution</h3>
                <p className="text-xs text-brand-muted">Active attack classification</p>
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
