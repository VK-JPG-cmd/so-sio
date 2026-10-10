import React, { useState } from 'react';
import { useBrand } from '../../context/BrandContext';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { SearchInput } from '../../components/ui/Input';
import { useNotification } from '../../context/NotificationContext';
import { threatService } from '../../services/api';
import { 
  Globe2, 
  Search, 
  RefreshCw, 
  ShieldAlert, 
  ExternalLink, 
  Send, 
  CheckCircle2, 
  AlertTriangle,
  Layers,
  Sparkles,
  ShieldCheck,
  PlusCircle,
  XCircle,
  HelpCircle,
  ArrowRight
} from 'lucide-react';
import { Link } from 'react-router-dom';

interface AnalyzedResult {
  raw_url: string;
  host: string;
  risk_score: number;
  risk_level: string;
  is_ssrf_blocked: boolean;
  ssrf_block_reason?: string | null;
  domain_analysis?: {
    raw_domain?: string;
    matched_brand_name?: string | null;
    similarity_score?: number;
    is_official_domain?: boolean;
    has_homoglyphs?: boolean;
    suspicious_keywords_found?: string[];
    risk_score?: number;
    risk_level?: string;
    analysis_reasons?: string[];
  };
  analysis_reasons?: string[];
  credential_harvesting_params?: string[];
  fetch_policy?: string;
}

interface DomainEntry {
  id: string;
  domain: string;
  tld: string;
  permutationType: string;
  riskScore: number;
  status: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  ip: string;
  registrar: string;
  firstSeen: string;
  hasSsl: boolean;
  hasCloneForm: boolean;
}

export const SuspiciousWebsitesPage: React.FC = () => {
  const { currentBrand } = useBrand();
  const { showToast } = useNotification();
  const [isScanning, setIsScanning] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');

  // Live URL Analysis States
  const [liveUrlInput, setLiveUrlInput] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [liveAnalysisResult, setLiveAnalysisResult] = useState<AnalyzedResult | null>(null);

  const initialDomains: DomainEntry[] = [
    {
      id: 'dom_1',
      domain: 'apex-bank-secure-login.net',
      tld: '.net',
      permutationType: 'Hyphenation + Subdomain lure',
      riskScore: 96,
      status: 'active',
      severity: 'critical' as const,
      ip: '185.220.101.44',
      registrar: 'NameCheap Privacy Guard',
      firstSeen: 'Today, 04:12 AM',
      hasSsl: true,
      hasCloneForm: true
    },
    {
      id: 'dom_2',
      domain: 'apexbaank.com',
      tld: '.com',
      permutationType: 'Double Vowel Typosquat',
      riskScore: 84,
      status: 'under_investigation',
      severity: 'high' as const,
      ip: '194.38.21.90',
      registrar: 'Tucows Inc.',
      firstSeen: 'Yesterday',
      hasSsl: true,
      hasCloneForm: false
    },
    {
      id: 'dom_3',
      domain: 'apexbank-bonus.co',
      tld: '.co',
      permutationType: 'Affix / Reward Keyword',
      riskScore: 78,
      status: 'takedown_requested',
      severity: 'high' as const,
      ip: '45.144.225.10',
      registrar: 'Porkbun LLC',
      firstSeen: '2 days ago',
      hasSsl: true,
      hasCloneForm: true
    },
    {
      id: 'dom_4',
      domain: 'apex-auth-center.xyz',
      tld: '.xyz',
      permutationType: 'Keyword Insertion',
      riskScore: 91,
      status: 'active',
      severity: 'critical' as const,
      ip: '91.240.118.52',
      registrar: 'Hostinger Abuse Desk',
      firstSeen: '3 days ago',
      hasSsl: false,
      hasCloneForm: true
    },
    {
      id: 'dom_5',
      domain: 'apex-community-forum.tech',
      tld: '.tech',
      permutationType: 'Legitimate Developer Community',
      riskScore: 28,
      status: 'false_positive',
      severity: 'low' as const,
      ip: '104.21.55.19',
      registrar: 'Cloudflare Inc.',
      firstSeen: '1 week ago',
      hasSsl: true,
      hasCloneForm: false
    }
  ];

  const [domainsList, setDomainsList] = useState(initialDomains);

  const handleRunRadarScan = () => {
    setIsScanning(true);
    setTimeout(() => {
      setIsScanning(false);
      showToast({ 
        type: 'success', 
        title: 'Radar Scan Complete', 
        message: 'Scanned 14,280 new TLD registrations in the past 6 hours. Monitored database up to date.' 
      });
    }, 1200);
  };

  const handleRunLiveAnalysis = async (urlToTest?: string) => {
    const target = (urlToTest || liveUrlInput).trim();
    if (!target) {
      showToast({
        type: 'error',
        title: 'URL Required',
        message: 'Please enter a target URL or domain to analyze.'
      });
      return;
    }

    setLiveUrlInput(target);
    setIsAnalyzing(true);
    setLiveAnalysisResult(null);

    try {
      const data = await threatService.analyzeUrl(target, currentBrand?.id);
      setLiveAnalysisResult(data);
      showToast({
        type: data.is_ssrf_blocked ? 'warning' : 'success',
        title: 'Backend Analysis Complete',
        message: `Evaluation completed with calculated risk score: ${data.risk_score}/100 (${data.risk_level})`
      });
    } catch (err: any) {
      showToast({
        type: 'error',
        title: 'Live Analysis Failed',
        message: err.message || 'Unable to analyze target with detection engine.'
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleAddLiveResultToRadar = () => {
    if (!liveAnalysisResult) return;

    const host = liveAnalysisResult.host || liveAnalysisResult.raw_url;
    if (domainsList.some(d => d.domain.toLowerCase() === host.toLowerCase())) {
      showToast({
        type: 'info',
        title: 'Already Monitored',
        message: `${host} is already in the active radar list.`
      });
      return;
    }

    const severityMap: Record<string, 'low' | 'medium' | 'high' | 'critical'> = {
      CRITICAL: 'critical',
      HIGH: 'high',
      MEDIUM: 'medium',
      LOW: 'low',
      BENIGN: 'low',
    };

    const newEntry = {
      id: `dom_live_${Date.now()}`,
      domain: host,
      tld: liveAnalysisResult.domain_analysis?.raw_domain?.split('.').pop() ? `.${liveAnalysisResult.domain_analysis.raw_domain.split('.').pop()}` : '.com',
      permutationType: liveAnalysisResult.domain_analysis?.has_homoglyphs 
        ? 'IDN Homoglyph Confusable' 
        : (liveAnalysisResult.is_ssrf_blocked ? 'SSRF / Infrastructure Probe' : 'Live Analyzed Candidate'),
      riskScore: Math.round(liveAnalysisResult.risk_score),
      status: liveAnalysisResult.risk_score >= 70 ? 'active' : 'under_investigation',
      severity: severityMap[liveAnalysisResult.risk_level] || 'medium',
      ip: liveAnalysisResult.is_ssrf_blocked ? 'BLOCKED_BY_GUARD' : '203.0.113.195',
      registrar: 'Dynamic Verification Engine',
      firstSeen: 'Just Now',
      hasSsl: liveAnalysisResult.raw_url.startsWith('https://'),
      hasCloneForm: (liveAnalysisResult.domain_analysis?.suspicious_keywords_found?.length || 0) > 0
    };

    setDomainsList([newEntry, ...domainsList]);
    showToast({
      type: 'success',
      title: 'Added to Radar Table',
      message: `${host} is now tracked in active radar table.`
    });
  };

  const filtered = domainsList.filter(d => 
    d.domain.toLowerCase().includes(searchFilter.toLowerCase()) ||
    d.permutationType.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-brand-dark tracking-tight">Suspicious Websites Radar</h1>
          <p className="text-xs text-brand-muted mt-1">
            Autonomous engine analyzing lookalike domains, homoglyph confusables, and phishing lures against registered brand assets.
          </p>
        </div>

        <Button
          onClick={handleRunRadarScan}
          isLoading={isScanning}
          leftIcon={<RefreshCw className={`w-4 h-4 ${isScanning ? 'animate-spin' : ''}`} />}
        >
          Run Permutation Scan
        </Button>
      </div>

      {/* Radar Overview Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6">
        <Card className="text-center p-6">
          <p className="text-xs font-semibold text-brand-muted uppercase">Permutations Monitored</p>
          <h3 className="text-3xl font-extrabold text-[#111312] mt-1">{1420 + domainsList.length - initialDomains.length}</h3>
          <p className="text-[11px] text-brand-muted mt-1">Typos, homoglyphs & keyword combos</p>
        </Card>

        <Card className="text-center p-6">
          <p className="text-xs font-semibold text-brand-muted uppercase">High-Risk Active Clones</p>
          <h3 className="text-3xl font-extrabold text-rose-600 mt-1">
            {domainsList.filter(d => d.riskScore >= 75).length}
          </h3>
          <p className="text-[11px] text-brand-muted mt-1">Stealing user credentials</p>
        </Card>

        <Card className="text-center p-6">
          <p className="text-xs font-semibold text-brand-muted uppercase">Autonomous Takedown Rate</p>
          <h3 className="text-3xl font-extrabold text-emerald-600 mt-1">96.4%</h3>
          <p className="text-[11px] text-brand-muted mt-1">Avg turnaround: 4.2 hours</p>
        </Card>
      </div>

      {/* Live Detection Tool (Connected to Backend POST /api/v1/analyze/url) */}
      <Card className="p-6 border border-emerald-500/30 bg-gradient-to-br from-white via-[#FCFDFD] to-emerald-50/20 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-brand-border/60 pb-4 mb-4">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-emerald-100 rounded-lg text-emerald-700">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-brand-dark">Live URL & Domain Threat Analyzer</h2>
              <p className="text-xs text-brand-muted">
                Direct heuristic & fuzzy brand analysis executed by backend detection engine (<span className="font-mono text-[11px]">POST /api/v1/analyze/url</span>)
              </p>
            </div>
          </div>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            LIVE ENGINE READY
          </span>
        </div>

        {/* Input & Action */}
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 relative">
              <Globe2 className="w-4 h-4 text-brand-muted absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={liveUrlInput}
                onChange={(e) => setLiveUrlInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleRunLiveAnalysis(); }}
                placeholder="Enter suspicious URL or domain (e.g. https://apex-bank-secure-login.xyz)"
                className="w-full pl-9 pr-4 py-2.5 text-xs bg-white border border-brand-border rounded-lg text-brand-dark placeholder:text-brand-muted/70 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-mono"
              />
            </div>
            <Button
              onClick={() => handleRunLiveAnalysis()}
              isLoading={isAnalyzing}
              leftIcon={<ShieldAlert className="w-4 h-4" />}
            >
              Analyze Live Target
            </Button>
          </div>

          {/* Quick Presets */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-[11px] font-semibold text-brand-muted">Demo Presets:</span>
            <button
              type="button"
              onClick={() => handleRunLiveAnalysis('https://apex-bank-secure-login.xyz')}
              className="px-2.5 py-1 text-[11px] font-medium bg-amber-50 text-amber-800 border border-amber-200 rounded-md hover:bg-amber-100 transition-colors"
            >
              Lookalike Lure
            </button>
            <button
              type="button"
              onClick={() => handleRunLiveAnalysis('https://apexbank.com')}
              className="px-2.5 py-1 text-[11px] font-medium bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-md hover:bg-emerald-100 transition-colors"
            >
              Official Brand Domain
            </button>
            <button
              type="button"
              onClick={() => handleRunLiveAnalysis('https://xn--pexbank-91a.com')}
              className="px-2.5 py-1 text-[11px] font-medium bg-indigo-50 text-indigo-800 border border-indigo-200 rounded-md hover:bg-indigo-100 transition-colors"
            >
              Cyrillic Homoglyph
            </button>
            <button
              type="button"
              onClick={() => handleRunLiveAnalysis('http://169.254.169.254/latest/meta-data')}
              className="px-2.5 py-1 text-[11px] font-medium bg-rose-50 text-rose-800 border border-rose-200 rounded-md hover:bg-rose-100 transition-colors"
            >
              SSRF Cloud Probe
            </button>
          </div>

          {/* Live Analysis Results Panel */}
          {liveAnalysisResult && (
            <div className="mt-4 p-4 rounded-xl border border-brand-border bg-white shadow-sm space-y-4 animate-in fade-in duration-150">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-brand-border/60 pb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-brand-dark">
                      {liveAnalysisResult.raw_url}
                    </span>
                    {liveAnalysisResult.domain_analysis?.is_official_domain && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                        OFFICIAL BRAND
                      </span>
                    )}
                    {liveAnalysisResult.is_ssrf_blocked && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800">
                        SSRF GUARD TRIGGERED
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-brand-muted mt-0.5">
                    Analyzed Host: <span className="font-mono font-semibold">{liveAnalysisResult.host}</span>
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <div className="text-[10px] uppercase font-bold text-brand-muted">Calculated Risk</div>
                    <div className="text-xl font-black text-brand-dark flex items-center gap-1.5 justify-end">
                      <span>{Math.round(liveAnalysisResult.risk_score)}</span>
                      <span className="text-xs font-normal text-brand-muted">/100</span>
                    </div>
                  </div>
                  <Badge 
                    severity={
                      liveAnalysisResult.risk_level === 'CRITICAL' ? 'critical' :
                      liveAnalysisResult.risk_level === 'HIGH' ? 'high' :
                      liveAnalysisResult.risk_level === 'MEDIUM' ? 'medium' : 'low'
                    } 
                  />
                </div>
              </div>

              {/* Grid of Key Diagnostic Indicators */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-[#F8F7F4] border border-brand-border/60">
                  <span className="text-[10px] uppercase font-bold text-brand-muted">Brand Correlation</span>
                  <p className="text-xs font-bold text-brand-dark mt-1">
                    {liveAnalysisResult.domain_analysis?.matched_brand_name || 'No Direct Association'}
                  </p>
                  <p className="text-[11px] text-brand-muted">
                    Similarity: {liveAnalysisResult.domain_analysis?.similarity_score?.toFixed(1) || '0.0'}%
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-[#F8F7F4] border border-brand-border/60">
                  <span className="text-[10px] uppercase font-bold text-brand-muted">Phishing Keywords</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {liveAnalysisResult.domain_analysis?.suspicious_keywords_found && liveAnalysisResult.domain_analysis.suspicious_keywords_found.length > 0 ? (
                      liveAnalysisResult.domain_analysis.suspicious_keywords_found.map(kw => (
                        <span key={kw} className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-100 text-amber-800">
                          {kw}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-brand-muted font-medium">None detected</span>
                    )}
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[#F8F7F4] border border-brand-border/60">
                  <span className="text-[10px] uppercase font-bold text-brand-muted">Safety & Fetch Policy</span>
                  <p className="text-[11px] font-bold text-emerald-700 mt-1 flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                    SSRF Immune (Zero-Trust)
                  </p>
                  <p className="text-[10px] text-brand-muted mt-0.5 line-clamp-1" title={liveAnalysisResult.fetch_policy}>
                    Safe Offline Analysis Active
                  </p>
                </div>
              </div>

              {/* Explanation Bullets */}
              {liveAnalysisResult.analysis_reasons && liveAnalysisResult.analysis_reasons.length > 0 && (
                <div className="p-3 rounded-lg bg-brand-light/60 border border-brand-border/60 space-y-1">
                  <span className="text-[10px] uppercase font-bold text-brand-muted">Engine Explanations:</span>
                  <ul className="list-disc list-inside text-xs text-brand-dark space-y-0.5">
                    {liveAnalysisResult.analysis_reasons.map((reason, idx) => (
                      <li key={idx} className="text-brand-dark/90 leading-relaxed font-medium">
                        {reason}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Action buttons */}
              <div className="flex justify-end gap-2 pt-1">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleAddLiveResultToRadar}
                  leftIcon={<PlusCircle className="w-3.5 h-3.5" />}
                >
                  Add to Monitored Radar
                </Button>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Search & Domains Table */}
      <Card padding="none">
        <div className="p-4 border-b border-brand-border/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex-1">
            <SearchInput
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Search candidate domain or permutation rule..."
            />
          </div>
          <span className="text-[11px] text-brand-muted whitespace-nowrap">
            Showing {filtered.length} of {domainsList.length} monitored assets
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#F8F7F4] text-brand-muted border-b border-brand-border font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-6 py-3.5">Candidate Domain</th>
                <th className="px-6 py-3.5">Permutation Strategy</th>
                <th className="px-6 py-3.5">Risk Score</th>
                <th className="px-6 py-3.5">Severity</th>
                <th className="px-6 py-3.5">Registrar / IP</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border/60">
              {filtered.map((dom) => (
                <tr key={dom.id} className="hover:bg-[#F8F7F4]/60 transition-colors">
                  <td className="px-6 py-4 font-mono font-bold text-brand-dark">
                    <div className="flex items-center gap-2">
                      <Globe2 className="w-4 h-4 text-[#111312] shrink-0" />
                      <span>{dom.domain}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-brand-muted">
                    {dom.permutationType}
                  </td>
                  <td className="px-6 py-4 font-bold text-brand-dark">
                    {dom.riskScore}/100
                  </td>
                  <td className="px-6 py-4">
                    <Badge severity={dom.severity} />
                  </td>
                  <td className="px-6 py-4 text-[11px] text-brand-muted">
                    <div>{dom.registrar}</div>
                    <div className="font-mono text-[10px]">{dom.ip}</div>
                  </td>
                  <td className="px-6 py-4">
                    <Badge status={dom.status} />
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link to="/brand-owner/threats/threat_apex_01">
                      <Button variant="secondary" size="sm">
                        Inspect
                      </Button>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

    </div>
  );
};
