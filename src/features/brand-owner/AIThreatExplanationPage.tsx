import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useBrand } from '../../context/BrandContext';
import { threatService } from '../../services/api';
import { SuspiciousThreat } from '../../types';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { 
  Sparkles, 
  ShieldCheck, 
  AlertTriangle, 
  Eye, 
  Globe2, 
  Lock, 
  ChevronDown, 
  ChevronUp, 
  ArrowRight,
  Send,
  Lightbulb,
  CheckCircle2
} from 'lucide-react';

export const AIThreatExplanationPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const { currentBrand } = useBrand();

  const [threats, setThreats] = useState<SuspiciousThreat[]>([]);
  const [selectedThreat, setSelectedThreat] = useState<SuspiciousThreat | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      try {
        if (currentBrand) {
          const list = await threatService.getThreats(currentBrand.id);
          setThreats(list);

          const targetId = searchParams.get('threatId') || list[0]?.id;
          const target = list.find(t => t.id === targetId) || list[0];
          setSelectedThreat(target || null);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [currentBrand, searchParams]);

  if (isLoading || !selectedThreat) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="w-10 h-10 border-3 border-[#111312] border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-brand-muted">Generating AI threat explanation...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-brand-dark tracking-tight">AI Threat Explanation</h1>
            <span className="text-xs font-bold text-[#111312] px-2.5 py-0.5 rounded-full bg-[#F4F3EF] border border-[#DCDAD4]">
              Plain English Analysis
            </span>
          </div>
          <p className="text-xs text-brand-muted mt-1">
            Understand exactly why our AI defense system detected and flagged this threat without technical jargon.
          </p>
        </div>

        {/* Threat Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-brand-muted">Inspecting Threat:</span>
          <select
            value={selectedThreat.id}
            onChange={(e) => {
              const target = threats.find(t => t.id === e.target.value);
              if (target) setSelectedThreat(target);
            }}
            className="px-3 py-2 text-xs font-bold rounded-2xl bg-white border border-brand-border text-brand-dark focus:outline-none focus:border-[#111312] max-w-xs truncate"
          >
            {threats.map((t) => (
              <option key={t.id} value={t.id}>
                {t.targetDomainOrUrl} ({t.category.replace(/_/g, ' ')})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Target Banner */}
      <div className="p-6 rounded-3xl bg-white border border-[#E2E1DC] shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold text-brand-muted uppercase">Target Analyzed</span>
            <Badge severity={selectedThreat.severity} size="sm" />
            <Badge status={selectedThreat.status} size="sm" />
          </div>
          <h2 className="text-lg sm:text-xl font-mono font-extrabold text-brand-dark">
            {selectedThreat.targetDomainOrUrl}
          </h2>
          <p className="text-xs text-brand-muted">
            Categorized as <strong className="text-brand-dark capitalize">{selectedThreat.category.replace(/_/g, ' ')}</strong> with AI Risk Score of <strong className="text-rose-600">{selectedThreat.riskScore}/100</strong>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link to={`/brand-owner/threats/${selectedThreat.id}`}>
            <Button variant="outline" size="sm">
              Threat Details
            </Button>
          </Link>
          <Link to={`/brand-owner/recommended-actions?threatId=${selectedThreat.id}`}>
            <Button size="sm">
              Recommended Actions
            </Button>
          </Link>
        </div>
      </div>

      {/* SECTION 1: Plain English AI Assessment */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Main 4 Plain-English Detection Reasons (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          
          <Card
            header={
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[#111312]" />
                <h3 className="text-sm font-bold text-brand-dark">How BrandShield AI Detected This Impersonation</h3>
              </div>
            }
          >
            <div className="space-y-4 pt-1 text-xs">
              
              {/* Reason 1: Lookalike Domain Name */}
              <div className="p-4 rounded-2xl bg-brand-surface-light border border-brand-border space-y-1.5">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-brand-dark text-xs flex items-center gap-1.5">
                    <Globe2 className="w-4 h-4 text-[#111312]" />
                    1. Deceptive Lookalike Domain
                  </h4>
                  <span className="text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full">
                    {selectedThreat.domainSimilarityScore}% Lexical Match
                  </span>
                </div>
                <p className="text-brand-muted leading-relaxed">
                  The creator registered a domain with subtle typographical mutations designed to look official at a glance (e.g., swapping letters, inserting double vowels, or appending "-login.net").
                </p>
              </div>

              {/* Reason 2: Visual & Logo Cloning */}
              <div className="p-4 rounded-2xl bg-brand-surface-light border border-brand-border space-y-1.5">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-brand-dark text-xs flex items-center gap-1.5">
                    <Eye className="w-4 h-4 text-[#111312]" />
                    2. Visual Trademark & Logo Copying
                  </h4>
                  <span className="text-[10px] font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full">
                    {selectedThreat.logoSimilarityScore}% Logo Match
                  </span>
                </div>
                <p className="text-brand-muted leading-relaxed">
                  Our computer vision scanner detected that the page uses your exact vector logo and brand color palette to fool visitors into trusting the site.
                </p>
              </div>

              {/* Reason 3: Fake Login / Credential Theft Form */}
              <div className="p-4 rounded-2xl bg-brand-surface-light border border-brand-border space-y-1.5">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-brand-dark text-xs flex items-center gap-1.5">
                    <Lock className="w-4 h-4 text-[#111312]" />
                    3. Credential Harvesting Forms
                  </h4>
                  <span className="text-[10px] font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full">
                    Active Phishing
                  </span>
                </div>
                <p className="text-brand-muted leading-relaxed">
                  The page contains fake login username, password, and two-factor SMS passcode entry fields that submit data to an unauthorized third-party server.
                </p>
              </div>

              {/* Reason 4: Urgency Social Engineering */}
              <div className="p-4 rounded-2xl bg-brand-surface-light border border-brand-border space-y-1.5">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-brand-dark text-xs flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-[#111312]" />
                    4. High-Urgency Pressure Language
                  </h4>
                  <span className="text-[10px] font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full">
                    NLP Detected
                  </span>
                </div>
                <p className="text-brand-muted leading-relaxed">
                  The copy uses urgent pressure tactics such as "Your account is temporarily suspended! Verify identity within 15 minutes to avoid complete freeze."
                </p>
              </div>

            </div>
          </Card>

        </div>

        {/* Right Column: Business Impact & Executive Takeaway (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          
          <Card
            header={
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <h3 className="text-xs font-bold text-brand-dark uppercase tracking-wider">Executive Takeaway</h3>
              </div>
            }
          >
            <div className="space-y-4 text-xs">
              <div>
                <span className="text-[10px] font-bold text-brand-muted uppercase">Risk Classification</span>
                <p className="text-sm font-bold text-rose-600 mt-0.5">High Potential Customer Impact</p>
                <p className="text-brand-muted text-[11px] mt-1 leading-relaxed">
                  If left active, customers searching for your portal or receiving phishing SMS links may surrender their credentials.
                </p>
              </div>

              <div className="pt-3 border-t border-brand-border space-y-2">
                <span className="text-[10px] font-bold text-brand-muted uppercase">Recommended Next Steps</span>
                <div className="space-y-2">
                  <div className="p-2.5 rounded-xl bg-brand-surface-light border border-brand-border text-brand-dark font-medium">
                    1. Submit Registrar Takedown Abuse Package
                  </div>
                  <div className="p-2.5 rounded-xl bg-brand-surface-light border border-brand-border text-brand-dark font-medium">
                    2. Add domain to browser Safe Browsing blocklists
                  </div>
                </div>
              </div>

              <Link to={`/brand-owner/recommended-actions?threatId=${selectedThreat.id}`} className="block pt-2">
                <Button className="w-full" size="sm">
                  Execute Action Plan
                </Button>
              </Link>
            </div>
          </Card>

        </div>

      </div>

    </div>
  );
};
