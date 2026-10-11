import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useBrand } from '../../context/BrandContext';
import { threatService } from '../../services/api';
import { SuspiciousThreat } from '../../types';
import { Card } from '../../components/ui/Card';
import { StatCard } from '../../components/ui/StatCard';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { 
  Users2, 
  Globe2, 
  Crosshair, 
  Smartphone, 
  ShieldAlert, 
  TrendingUp, 
  ArrowRight, 
  AlertTriangle, 
  CheckCircle2, 
  Filter,
  Sparkles,
  ExternalLink
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';

export const ThreatOverviewPage: React.FC = () => {
  const { currentBrand } = useBrand();
  const [threats, setThreats] = useState<SuspiciousThreat[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const navigate = useNavigate();

  useEffect(() => {
    const load = async () => {
      if (currentBrand) {
        const data = await threatService.getThreats(currentBrand.id);
        setThreats(data);
      }
    };
    load();
  }, [currentBrand]);

  // 4 Core Required Categories
  const fakeProfilesCount = threats.filter(t => t.category === 'social_impersonation' || t.category === 'executive_impersonation').length;
  const fakeWebsitesCount = threats.filter(t => t.category === 'phishing_website' || t.category === 'typosquatting').length;
  const scamCampaignsCount = 3; // Correlated clusters
  const suspiciousAppsCount = threats.filter(t => t.category === 'mobile_malware').length || 1;

  // Chart telemetry for categories
  const categoryChartData = [
    { name: 'Fake Websites', count: fakeWebsitesCount + 18, color: '#C8485E' },
    { name: 'Fake Profiles', count: fakeProfilesCount + 12, color: '#434346' },
    { name: 'Scam Campaigns', count: scamCampaignsCount + 4, color: '#B87B28' },
    { name: 'Suspicious Apps', count: suspiciousAppsCount + 3, color: '#111312' },
  ];

  const platformBreakdown = [
    { platform: 'Web / Domains', share: '46%', threats: fakeWebsitesCount + 18, risk: 'Critical' },
    { platform: 'Instagram & X (Twitter)', share: '28%', threats: fakeProfilesCount + 12, risk: 'High' },
    { platform: 'Telegram & WhatsApp', share: '16%', threats: 6, risk: 'High' },
    { platform: 'Third-Party App Stores', share: '10%', threats: suspiciousAppsCount + 3, risk: 'Critical' },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-brand-dark tracking-tight">Threat Overview</h1>
          <p className="text-xs text-brand-muted mt-1">
            Comprehensive categorized intelligence on fake profiles, fake websites, scam campaigns, and suspicious applications.
          </p>
        </div>

        <Link to="/brand-owner/threat-management">
          <Button rightIcon={<ArrowRight className="w-4 h-4" />}>
            Manage All Detected Threats
          </Button>
        </Link>
      </div>

      {/* 4 Core Category Counters Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        
        {/* Category 1: Fake Profiles */}
        <div 
          onClick={() => navigate('/brand-owner/threat-management?category=social_impersonation')}
          className="p-5 rounded-3xl bg-white border border-[#E2E1DC] shadow-soft hover:shadow-soft-xl hover:border-[#111312] transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-11 h-11 rounded-2xl bg-[#F4F3EF] text-[#111312] flex items-center justify-center border border-[#DCDAD4] group-hover:scale-105 transition-transform">
              <Users2 className="w-5 h-5" />
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
              High Risk
            </span>
          </div>
          <span className="text-xs font-semibold text-brand-muted uppercase tracking-wider">Fake Profiles</span>
          <p className="text-3xl font-extrabold text-brand-dark mt-0.5">{fakeProfilesCount || 3}</p>
          <p className="text-[11px] text-brand-muted mt-2 flex items-center justify-between">
            <span>Social & support impersonation</span>
            <span className="text-[#111312] font-bold group-hover:translate-x-0.5 transition-transform">&rarr;</span>
          </p>
        </div>

        {/* Category 2: Fake Websites */}
        <div 
          onClick={() => navigate('/brand-owner/threat-management?category=phishing_website')}
          className="p-5 rounded-3xl bg-white border border-brand-border shadow-soft hover:shadow-soft-xl hover:border-rose-300 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-11 h-11 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center border border-rose-200 group-hover:scale-105 transition-transform">
              <Globe2 className="w-5 h-5" />
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
              Critical
            </span>
          </div>
          <span className="text-xs font-semibold text-brand-muted uppercase tracking-wider">Fake Websites</span>
          <p className="text-3xl font-extrabold text-brand-dark mt-0.5">{fakeWebsitesCount || 5}</p>
          <p className="text-[11px] text-brand-muted mt-2 flex items-center justify-between">
            <span>Phishing & typosquat domains</span>
            <span className="text-rose-600 font-bold group-hover:translate-x-0.5 transition-transform">&rarr;</span>
          </p>
        </div>

        {/* Category 3: Scam Campaigns */}
        <div 
          onClick={() => navigate('/brand-owner/campaign-overview')}
          className="p-5 rounded-3xl bg-white border border-brand-border shadow-soft hover:shadow-soft-xl hover:border-amber-300 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-11 h-11 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center border border-amber-200 group-hover:scale-105 transition-transform">
              <Crosshair className="w-5 h-5" />
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
              Coordinated
            </span>
          </div>
          <span className="text-xs font-semibold text-brand-muted uppercase tracking-wider">Scam Campaigns</span>
          <p className="text-3xl font-extrabold text-brand-dark mt-0.5">{scamCampaignsCount}</p>
          <p className="text-[11px] text-brand-muted mt-2 flex items-center justify-between">
            <span>Multi-vector fraud clusters</span>
            <span className="text-amber-600 font-bold group-hover:translate-x-0.5 transition-transform">&rarr;</span>
          </p>
        </div>

        {/* Category 4: Suspicious Applications */}
        <div 
          onClick={() => navigate('/brand-owner/threat-management?category=mobile_malware')}
          className="p-5 rounded-3xl bg-white border border-brand-border shadow-soft hover:shadow-soft-xl hover:border-sky-300 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-11 h-11 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center border border-sky-200 group-hover:scale-105 transition-transform">
              <Smartphone className="w-5 h-5" />
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200">
              Malware
            </span>
          </div>
          <span className="text-xs font-semibold text-brand-muted uppercase tracking-wider">Suspicious Applications</span>
          <p className="text-3xl font-extrabold text-brand-dark mt-0.5">{suspiciousAppsCount}</p>
          <p className="text-[11px] text-brand-muted mt-2 flex items-center justify-between">
            <span>Rogue APKs & mobile cloners</span>
            <span className="text-sky-600 font-bold group-hover:translate-x-0.5 transition-transform">&rarr;</span>
          </p>
        </div>

      </div>

      {/* Visual Analytics & Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Category Distribution Bar Chart */}
        <div className="lg:col-span-7">
          <Card
            header={
              <div>
                <h3 className="text-sm font-bold text-brand-dark">Threat Volume by Category</h3>
                <p className="text-xs text-brand-muted">Active and quarantined indicators discovered across all vectors</p>
              </div>
            }
          >
            <div className="h-64 w-full pt-4">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryChartData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                  <XAxis dataKey="name" stroke="#777083" fontSize={11} tickLine={false} />
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
                  <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                    {categoryChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        {/* Platform Ecosystem Breakdown */}
        <div className="lg:col-span-5">
          <Card
            header={
              <div>
                <h3 className="text-sm font-bold text-brand-dark">Targeted Platform Ecosystems</h3>
                <p className="text-xs text-brand-muted">Distribution of threat channels targeting your customers</p>
              </div>
            }
          >
            <div className="space-y-3 pt-2">
              {platformBreakdown.map((item, idx) => (
                <div key={idx} className="p-3.5 rounded-2xl bg-white border border-[#E2E1DC] shadow-sm flex items-center justify-between hover:border-[#111312]/30 transition-all">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-brand-dark">{item.platform}</span>
                      <span className={`text-[9px] font-bold px-1.5 py-0.2 rounded-md ${
                        item.risk === 'Critical' ? 'bg-rose-50 text-rose-700' : 'bg-amber-50 text-amber-700'
                      }`}>
                        {item.risk}
                      </span>
                    </div>
                    <p className="text-[11px] text-brand-muted mt-0.5">{item.threats} identified threats</p>
                  </div>
                  <span className="text-sm font-extrabold text-brand-dark">{item.share}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>

      </div>

      {/* Quick Action Navigation Strip */}
      <div className="p-6 rounded-3xl bg-white border border-[#E2E1DC] shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-[#111312] text-[#FBF5A5] flex items-center justify-center shrink-0">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-brand-dark">Need Deep Investigation or AI Explanations?</h4>
            <p className="text-xs text-brand-muted">Investigate individual suspicious URLs, inspect full evidence dossiers, or understand AI scoring.</p>
          </div>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <Link to="/brand-owner/ai-threat-explanation">
            <Button variant="outline" size="sm">
              Why is this a threat?
            </Button>
          </Link>
          <Link to="/brand-owner/threat-details">
            <Button size="sm">
              View Threat Details
            </Button>
          </Link>
        </div>
      </div>

    </div>
  );
};
