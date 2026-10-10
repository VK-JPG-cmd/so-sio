import React, { useState } from 'react';
import { useBrand } from '../../context/BrandContext';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  Calendar, 
  ShieldAlert, 
  CheckCircle2, 
  Lightbulb, 
  ArrowRight,
  Globe2,
  Users2,
  Smartphone,
  Sparkles
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend 
} from 'recharts';

export const RiskTrendsPage: React.FC = () => {
  const { currentBrand } = useBrand();
  const [timeframe, setTimeframe] = useState<'7d' | '30d' | '90d' | '1y'>('30d');

  // Historical Telemetry Data
  const trendDataMap = {
    '7d': [
      { date: 'Oct 3', riskScore: 74, webThreats: 14, socialThreats: 8, mobileThreats: 2 },
      { date: 'Oct 4', riskScore: 76, webThreats: 16, socialThreats: 9, mobileThreats: 2 },
      { date: 'Oct 5', riskScore: 79, webThreats: 19, socialThreats: 11, mobileThreats: 3 },
      { date: 'Oct 6', riskScore: 85, webThreats: 26, socialThreats: 14, mobileThreats: 4 },
      { date: 'Oct 7', riskScore: 84, webThreats: 24, socialThreats: 13, mobileThreats: 4 },
      { date: 'Oct 8', riskScore: 81, webThreats: 21, socialThreats: 10, mobileThreats: 3 },
      { date: 'Oct 9', riskScore: 82, webThreats: 22, socialThreats: 11, mobileThreats: 3 },
    ],
    '30d': [
      { date: 'Sep 10', riskScore: 68, webThreats: 10, socialThreats: 6, mobileThreats: 1 },
      { date: 'Sep 15', riskScore: 72, webThreats: 14, socialThreats: 8, mobileThreats: 2 },
      { date: 'Sep 20', riskScore: 69, webThreats: 12, socialThreats: 7, mobileThreats: 1 },
      { date: 'Sep 25', riskScore: 75, webThreats: 17, socialThreats: 10, mobileThreats: 2 },
      { date: 'Sep 30', riskScore: 78, webThreats: 20, socialThreats: 12, mobileThreats: 3 },
      { date: 'Oct 5', riskScore: 85, webThreats: 27, socialThreats: 15, mobileThreats: 4 },
      { date: 'Oct 9', riskScore: 82, webThreats: 22, socialThreats: 11, mobileThreats: 3 },
    ],
    '90d': [
      { date: 'Jul', riskScore: 62, webThreats: 28, socialThreats: 18, mobileThreats: 4 },
      { date: 'Aug', riskScore: 66, webThreats: 32, socialThreats: 22, mobileThreats: 5 },
      { date: 'Sep', riskScore: 74, webThreats: 48, socialThreats: 31, mobileThreats: 8 },
      { date: 'Oct', riskScore: 82, webThreats: 61, socialThreats: 38, mobileThreats: 11 },
    ],
    '1y': [
      { date: 'Q4 2025', riskScore: 55, webThreats: 40, socialThreats: 20, mobileThreats: 5 },
      { date: 'Q1 2026', riskScore: 58, webThreats: 52, socialThreats: 26, mobileThreats: 7 },
      { date: 'Q2 2026', riskScore: 64, webThreats: 68, socialThreats: 35, mobileThreats: 9 },
      { date: 'Q3 2026', riskScore: 76, webThreats: 94, socialThreats: 52, mobileThreats: 14 },
      { date: 'Q4 2026', riskScore: 82, webThreats: 112, socialThreats: 64, mobileThreats: 18 },
    ],
  };

  const currentData = trendDataMap[timeframe];

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-brand-dark tracking-tight">Risk Trends</h1>
          <p className="text-xs text-brand-muted mt-1">
            Historical digital risk evaluation, threat trajectory indicators, and plain-English intelligence summaries.
          </p>
        </div>

        {/* Timeframe Selector */}
        <div className="flex items-center gap-1.5 p-1 rounded-2xl bg-white border border-brand-border">
          {(['7d', '30d', '90d', '1y'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTimeframe(t)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold uppercase transition-all ${
                timeframe === t
                  ? 'bg-[#111312] text-[#FBF5A5] border border-[#111312] shadow-sm'
                  : 'text-brand-muted hover:text-brand-dark'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Trajectory Status Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        
        {/* Risk Trend Status Banner */}
        <Card className="p-5">
          <span className="text-[10px] font-bold text-brand-muted uppercase tracking-wider block mb-1">
            Current Risk Trajectory
          </span>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-extrabold text-rose-600">+4.2%</span>
            <span className="px-2.5 py-0.5 rounded-full bg-rose-50 text-rose-700 text-xs font-bold border border-rose-200 flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5" /> INCREASING
            </span>
          </div>
          <p className="text-xs text-brand-muted mt-2">
            Digital risk has increased over the past 30 days due to a coordinated phishing syndicate.
          </p>
        </Card>

        {/* Fastest Growing Vector */}
        <Card className="p-5">
          <span className="text-[10px] font-bold text-brand-muted uppercase tracking-wider block mb-1">
            Fastest Growing Attack Vector
          </span>
          <div className="flex items-center gap-2">
            <Globe2 className="w-5 h-5 text-rose-500" />
            <span className="text-lg font-extrabold text-brand-dark">Domain Typosquats</span>
          </div>
          <p className="text-xs text-brand-muted mt-2">
            Lookalike domain registrations rose by +38% following bulk registrar provisioning.
          </p>
        </Card>

        {/* Mitigation Velocity */}
        <Card className="p-5">
          <span className="text-[10px] font-bold text-brand-muted uppercase tracking-wider block mb-1">
            Takedown Mitigation Velocity
          </span>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <span className="text-lg font-extrabold text-emerald-700">4.2 Hours Avg.</span>
          </div>
          <p className="text-xs text-brand-muted mt-2">
            Fast-track registrar enforcement resolved 98% of reported phishing domains.
          </p>
        </Card>

      </div>

      {/* Interactive Risk Over Time Chart */}
      <Card
        header={
          <div className="flex items-center justify-between w-full">
            <div>
              <h3 className="text-sm font-bold text-brand-dark">Digital Risk Index Over Time</h3>
              <p className="text-xs text-brand-muted">Aggregated composite risk score tracking domain, profile, and malware vectors</p>
            </div>
          </div>
        }
      >
        <div className="h-72 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={currentData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#C84D62" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#C84D62" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" stroke="#777083" fontSize={11} tickLine={false} />
              <YAxis domain={[40, 100]} stroke="#777083" fontSize={11} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#FFFFFF',
                  borderRadius: '16px',
                  border: '1px solid #E2E1DC',
                  boxShadow: '0 10px 25px rgba(17, 19, 18, 0.08)',
                  fontSize: '12px'
                }}
              />
              <Area type="monotone" dataKey="riskScore" stroke="#C84D62" strokeWidth={3} fillOpacity={1} fill="url(#riskGrad)" name="Risk Score (0-100)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Plain English Executive Summaries of Important Changes */}
      <Card
        header={
          <div className="flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-[#111312]" />
            <h3 className="text-sm font-bold text-brand-dark">Summary of Important Changes (Plain English)</h3>
          </div>
        }
      >
        <div className="space-y-3 pt-1">
          
          <div className="p-4 rounded-2xl bg-brand-surface-light border border-brand-border space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-brand-dark">1. Phishing Domain Spike (Thursday, Oct 6)</span>
              <span className="text-[10px] font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full">Elevated Threat</span>
            </div>
            <p className="text-xs text-brand-muted leading-relaxed">
              Phishing activity increased significantly after 3 deceptive domains (`apex-bank-secure-login.net`, `apexbaank.com`) were registered across bulletproof registrars.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-brand-surface-light border border-brand-border space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-brand-dark">2. Social Media Impersonation Stabilized</span>
              <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full">Stabilizing</span>
            </div>
            <p className="text-xs text-brand-muted leading-relaxed">
              Following takedowns on X and Instagram, fake customer support bot activity decreased by 22% over the weekend.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-brand-surface-light border border-brand-border space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-brand-dark">3. Mobile App Threat Containment</span>
              <span className="text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full">Under Takedown</span>
            </div>
            <p className="text-xs text-brand-muted leading-relaxed">
              Google Play Protect and third-party APK mirrors have been notified with the SHA-256 signature of the rogue banking app.
            </p>
          </div>

        </div>
      </Card>

    </div>
  );
};
