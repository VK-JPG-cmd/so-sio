import React, { useState, useEffect } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { useBrand } from '../../context/BrandContext';
import { threatService } from '../../services/api';
import { ThreatCampaign, SuspiciousThreat } from '../../types';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { useNotification } from '../../context/NotificationContext';
import { 
  ArrowLeft, 
  Crosshair, 
  Workflow, 
  Share2, 
  Globe2, 
  Smartphone, 
  Database, 
  ArrowRight, 
  Clock, 
  CheckCircle2, 
  AlertTriangle, 
  AlertOctagon, 
  ShieldAlert, 
  ExternalLink, 
  Send, 
  Layers, 
  Sparkles, 
  Lock,
  Filter,
  HelpCircle,
  Server,
  FileCode,
  ShieldCheck,
  ChevronRight,
  ListChecks,
  Radio,
  Copy,
  Info
} from 'lucide-react';
import confetti from 'canvas-confetti';

export const CampaignDetailPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const { currentBrand } = useBrand();
  const { showToast } = useNotification();
  const navigate = useNavigate();

  const [campaigns, setCampaigns] = useState<ThreatCampaign[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<ThreatCampaign | null>(null);
  const [activeStep, setActiveStep] = useState<number>(1);
  const [evidenceFilter, setEvidenceFilter] = useState<string>('all');
  const [showGlossary, setShowGlossary] = useState<boolean>(false);
  const [actionStatuses, setActionStatuses] = useState<Record<string, string>>({
    act_1: 'Dispatched',
    act_2: 'Ready to Execute',
    act_3: 'Ready to Execute',
    act_4: 'In Progress',
    act_5: 'Active',
    act_6: 'Active'
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      try {
        if (currentBrand) {
          const list = await threatService.getCampaigns(currentBrand.id);
          setCampaigns(list);

          const targetId = searchParams.get('campaignId') || list[0]?.id;
          const target = list.find(c => c.id === targetId) || list[0];
          setSelectedCampaign(target || null);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [currentBrand, searchParams]);

  if (isLoading || !selectedCampaign) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="w-10 h-10 border-3 border-[#111312] border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-[#434346]">Loading campaign attack-flow diagram...</p>
      </div>
    );
  }

  // Visual Attack-Flow Steps
  const attackSteps = [
    {
      id: 1,
      title: 'Social Media Lure',
      icon: Share2,
      platform: 'Instagram & X (Twitter)',
      entity: '@ApexBankHelp_Official (Spoofed Bot)',
      description: 'Attacker creates fake support handles and publishes automated direct replies to customers promising cash incentives or instant account unlocks.',
      risk: 'Initial Customer Entrypoint',
      threatId: 'threat_apex_03',
      category: 'social',
      iocs: ['@ApexBankHelp_Official', 't.me/apex_claims_bot']
    },
    {
      id: 2,
      title: 'Phishing Landing Page',
      icon: Globe2,
      platform: 'Web / Deceptive Domain',
      entity: 'apex-bank-secure-login.net/verify',
      description: 'Lure directs victims to a lookalike website imitating ApexBank with 94% visual accuracy to harvest banking credentials and 2FA SMS tokens.',
      risk: 'Credential Harvesting',
      threatId: 'threat_apex_01',
      category: 'web',
      iocs: ['apex-bank-secure-login.net', '185.220.101.44']
    },
    {
      id: 3,
      title: 'Suspicious Android App',
      icon: Smartphone,
      platform: 'Android Package (APK)',
      entity: 'ApexBank Mobile Assistant v2.1.0',
      description: 'Website prompts mobile visitors to download an untrusted "security update APK" containing Trojanized banking overlay malware.',
      risk: 'Malware Sideloading',
      threatId: 'threat_apex_04',
      category: 'apk',
      iocs: ['com.apexbank.assistant.apk', 'SHA256: 8a7f4e91...b320']
    },
    {
      id: 4,
      title: 'Data Exfiltration Server',
      icon: Database,
      platform: 'Offshore C2 Infrastructure',
      entity: 'gate-collector.xyz/api/v1/dump',
      description: 'Malware exfiltrates intercepted SMS verification passcodes and live keystrokes directly to the attacker’s command-and-control server.',
      risk: 'Account Takeover Threat',
      threatId: 'threat_apex_02',
      category: 'c2',
      iocs: ['gate-collector.xyz', '194.26.29.118 (NL)']
    }
  ];

  // Comprehensive Evidence Items
  const evidenceItems = [
    {
      id: 'ev_1',
      category: 'web',
      type: 'Phishing Domain & Cloned Portal',
      entity: 'https://apex-bank-secure-login.net/verify',
      riskScore: 96,
      status: 'Active (Takedown Pending)',
      detectedAt: 'Oct 9, 2026',
      confidence: 98,
      source: 'Automated Crawler',
      threatId: 'threat_apex_01',
      plainDesc: 'Exact visual replica of ApexBank login interface hosted on bulletproof VPS.'
    },
    {
      id: 'ev_2',
      category: 'social',
      type: 'Social Impersonation Handle',
      entity: '@ApexBankHelp_Official (Twitter/X)',
      riskScore: 91,
      status: 'Escalated to X Trust & Safety',
      detectedAt: 'Oct 8, 2026',
      confidence: 94,
      source: 'Community Report #REP-1002',
      threatId: 'threat_apex_03',
      plainDesc: 'Automated bot profile posting fake urgent phone numbers in replies to customer tweets.'
    },
    {
      id: 'ev_3',
      category: 'apk',
      type: 'Trojanized Mobile APK',
      entity: 'ApexBank_Mobile_Assistant_v2.1.apk',
      riskScore: 98,
      status: 'Blacklisted & Flagged',
      detectedAt: 'Oct 7, 2026',
      confidence: 99,
      source: 'Threat Intelligence Feed',
      threatId: 'threat_apex_04',
      plainDesc: 'Banking trojan overlay requesting SMS permissions to intercept OTP login passcodes.'
    },
    {
      id: 'ev_4',
      category: 'c2',
      type: 'Command & Control Endpoint',
      entity: 'https://gate-collector.xyz/api/v1/dump (194.26.29.118)',
      riskScore: 94,
      status: 'Under Investigation',
      detectedAt: 'Oct 6, 2026',
      confidence: 96,
      source: 'DNS Telemetry Engine',
      threatId: 'threat_apex_02',
      plainDesc: 'Backend server receiving exfiltrated credentials from the malicious APK package.'
    }
  ];

  const filteredEvidence = evidenceFilter === 'all' 
    ? evidenceItems 
    : evidenceItems.filter(e => e.category === evidenceFilter);

  const handleDisruptCampaign = () => {
    confetti({ particleCount: 80, spread: 70 });
    showToast({
      type: 'success',
      title: 'Coordinated Takedown Dispatched',
      message: `Abuse notices successfully submitted to all registrars, social networks, and hosting providers associated with ${selectedCampaign.name}.`
    });
  };

  const handleExecuteAction = (actionId: string, title: string) => {
    setActionStatuses(prev => ({ ...prev, [actionId]: 'Dispatched' }));
    confetti({ particleCount: 40, spread: 50 });
    showToast({
      type: 'success',
      title: 'Action Triggered',
      message: `${title} has been successfully dispatched.`
    });
  };

  const currentStep = attackSteps.find(s => s.id === activeStep) || attackSteps[0];
  const StepIcon = currentStep.icon;

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* ================= 1. TOP HEADER & BREADCRUMB ================= */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#E2E1DC]">
        <div className="flex flex-wrap items-center gap-3">
          <Link
            to="/brand-owner/campaign-overview"
            className="inline-flex items-center gap-1.5 text-xs font-bold text-[#434346] hover:text-[#111312] transition-colors bg-white px-3 py-1.5 rounded-xl border border-[#E2E1DC]"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Campaign Overview</span>
          </Link>

          {/* Campaign Selector Dropdown */}
          {campaigns.length > 1 && (
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold text-[#434346] uppercase">Campaign:</span>
              <select
                value={selectedCampaign.id}
                onChange={(e) => {
                  const target = campaigns.find(c => c.id === e.target.value);
                  if (target) setSelectedCampaign(target);
                }}
                className="px-3 py-1.5 text-xs font-bold rounded-xl bg-white border border-[#E2E1DC] text-[#111312] focus:outline-none focus:border-[#111312] max-w-[260px] truncate shadow-xs"
              >
                {campaigns.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <a href="#action-plan">
            <Button variant="outline" size="sm" leftIcon={<ListChecks className="w-3.5 h-3.5" />}>
              Recommended Action Plan
            </Button>
          </a>

          <Button size="sm" onClick={handleDisruptCampaign} leftIcon={<Send className="w-4 h-4" />}>
            Disrupt Entire Campaign
          </Button>
        </div>
      </div>

      {/* ================= 2. CAMPAIGN IDENTITY HEADER ================= */}
      <div className="p-6 sm:p-7 rounded-3xl bg-white border border-[#E2E1DC] shadow-soft space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <div className="p-2 rounded-xl bg-[#111312] text-[#FBF5A5] border border-[#2B2D2C]">
                <Crosshair className="w-4 h-4" />
              </div>
              <span className="text-[10px] font-black text-[#111312] uppercase tracking-wider">Correlated Threat Campaign</span>
              <Badge severity={selectedCampaign.severity} size="sm" />
              <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                selectedCampaign.status === 'active' 
                  ? 'bg-rose-50 text-rose-700 border border-rose-200' 
                  : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              }`}>
                {selectedCampaign.status.toUpperCase()}
              </span>
            </div>

            <h1 className="text-xl sm:text-2xl font-black text-[#111312] tracking-tight">
              {selectedCampaign.name}
            </h1>

            <p className="text-xs text-[#434346] max-w-3xl leading-relaxed">
              Attributed Threat Actor: <strong className="text-[#111312]">{selectedCampaign.threatActor || 'Unclassified Threat Cluster'}</strong> &bull; Detected on {new Date(selectedCampaign.detectedAt).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}
            </p>

            <div className="p-3.5 rounded-2xl bg-[#F8F7F4] border border-[#E2E1DC] text-xs text-[#434346] leading-relaxed max-w-4xl">
              <span className="font-bold text-[#111312] mr-1">Executive Summary:</span>
              {selectedCampaign.summary}
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-rose-50/80 border border-rose-200 text-xs space-y-1.5 shrink-0 max-w-sm">
            <span className="text-[10px] font-bold text-rose-800 uppercase tracking-wider flex items-center gap-1.5">
              <AlertOctagon className="w-4 h-4 text-rose-600" /> Customer Risk Exposure
            </span>
            <p className="text-base font-black text-rose-950">
              ~{selectedCampaign.affectedCustomerCountEst.toLocaleString()} Potential Victims
            </p>
            <p className="text-[11px] text-rose-800 leading-snug">
              Coordinated lures targeting credentials and accounts across {selectedCampaign.targetedRegions.join(', ')}.
            </p>
          </div>
        </div>
      </div>

      {/* ================= 3. KEY FACTS STRIP ================= */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
        <div className="p-3.5 rounded-2xl bg-white border border-[#E2E1DC] shadow-soft">
          <span className="text-[10px] font-bold text-[#434346] uppercase tracking-wider block">1. Threat Severity</span>
          <div className="mt-1 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-600" />
            <span className="text-sm font-black text-[#111312] capitalize">{selectedCampaign.severity} Tier</span>
          </div>
          <span className="text-[10px] text-[#434346] mt-0.5 block">Immediate takedown priority</span>
        </div>

        <div className="p-3.5 rounded-2xl bg-white border border-[#E2E1DC] shadow-soft">
          <span className="text-[10px] font-bold text-[#434346] uppercase tracking-wider block">2. Status</span>
          <div className="mt-1 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
            <span className="text-sm font-black text-[#111312] capitalize">{selectedCampaign.status}</span>
          </div>
          <span className="text-[10px] text-[#434346] mt-0.5 block">Real-time lure distribution</span>
        </div>

        <div className="p-3.5 rounded-2xl bg-white border border-[#E2E1DC] shadow-soft">
          <span className="text-[10px] font-bold text-[#434346] uppercase tracking-wider block">3. Correlated Assets</span>
          <div className="mt-1">
            <span className="text-sm font-black text-[#111312]">25 Entities</span>
          </div>
          <span className="text-[10px] text-[#434346] mt-0.5 block">Across 4 distinct attack channels</span>
        </div>

        <div className="p-3.5 rounded-2xl bg-white border border-[#E2E1DC] shadow-soft">
          <span className="text-[10px] font-bold text-[#434346] uppercase tracking-wider block">4. Victim Footprint</span>
          <div className="mt-1">
            <span className="text-sm font-black text-[#111312]">~{selectedCampaign.affectedCustomerCountEst.toLocaleString()}</span>
          </div>
          <span className="text-[10px] text-[#434346] mt-0.5 block">Targeted customer accounts</span>
        </div>

        <div className="p-3.5 rounded-2xl bg-white border border-[#E2E1DC] shadow-soft col-span-2 md:col-span-1">
          <span className="text-[10px] font-bold text-[#434346] uppercase tracking-wider block">5. Linked Evidence</span>
          <div className="mt-1">
            <span className="text-sm font-black text-[#111312]">4 Pieces of Technical Evidence</span>
          </div>
          <span className="text-[10px] text-[#434346] mt-0.5 block">Websites, IPs & file evidence</span>
        </div>
      </div>

      {/* ================= 4. INTERACTIVE ATTACK-FLOW DIAGRAM ================= */}
      <Card
        header={
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <div className="flex items-center gap-2">
                <Workflow className="w-4 h-4 text-[#111312]" />
                <h3 className="text-base font-extrabold text-[#111312]">Interactive Attack-Flow Diagram</h3>
              </div>
              <p className="text-xs text-[#434346] mt-0.5">
                Click any stage along the progression to inspect how the threat actors funnel victims from social lures to backend exfiltration.
              </p>
            </div>
            <span className="text-[11px] font-semibold text-[#434346] bg-[#F4F3EF] px-3 py-1 rounded-xl border border-[#DCDAD4] shrink-0">
              Active Stage: 0{activeStep} of 04
            </span>
          </div>
        }
      >
        <div className="space-y-6 pt-2">
          
          {/* Stepper Nodes */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
            {attackSteps.map((step, idx) => {
              const Icon = step.icon;
              const isSelected = activeStep === step.id;

              return (
                <div
                  key={step.id}
                  onClick={() => setActiveStep(step.id)}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer relative ${
                    isSelected 
                      ? 'bg-[#111312] text-[#FBF5A5] border-[#111312] shadow-md' 
                      : 'bg-white border-[#E2E1DC] hover:border-[#111312]/40 text-[#111312]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${
                      isSelected ? 'bg-[#FBF5A5] text-[#111312]' : 'bg-[#F4F3EF] text-[#434346] border border-[#DCDAD4]'
                    }`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className={`text-[10px] font-mono font-bold ${isSelected ? 'text-[#FBF5A5]/80' : 'text-[#434346]'}`}>
                      Stage 0{step.id}
                    </span>
                  </div>

                  <h4 className="text-xs font-bold truncate">{step.title}</h4>
                  <p className={`text-[11px] truncate mt-0.5 ${isSelected ? 'text-[#DCDCDA]' : 'text-[#434346]'}`}>
                    {step.platform}
                  </p>

                  <div className={`mt-3 pt-2 border-t flex items-center justify-between text-[10px] ${
                    isSelected ? 'border-white/10' : 'border-[#E2E1DC]'
                  }`}>
                    <span className="font-bold text-rose-500">{step.risk}</span>
                    <span className={`font-bold ${isSelected ? 'text-[#FBF5A5]' : 'text-[#111312]'}`}>&rarr;</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Active Node Detail Inspector */}
          <div className="p-5 sm:p-6 rounded-3xl bg-[#F8F7F4] border border-[#E2E1DC] space-y-4 animate-in fade-in duration-150">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#E2E1DC]">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-2xl bg-[#111312] text-[#FBF5A5]">
                  <StepIcon className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] font-bold text-[#434346] uppercase tracking-wider">{currentStep.platform}</span>
                  <h4 className="text-sm font-extrabold text-[#111312]">
                    Stage 0{currentStep.id}: {currentStep.title} &mdash; <span className="font-mono text-[#111312]">{currentStep.entity}</span>
                  </h4>
                </div>
              </div>

              <Link to={`/brand-owner/threats/${currentStep.threatId}`}>
                <Button variant="secondary" size="sm" rightIcon={<ExternalLink className="w-3.5 h-3.5" />}>
                  Investigate Threat Details
                </Button>
              </Link>
            </div>

            <p className="text-xs text-[#434346] leading-relaxed">
              {currentStep.description}
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs pt-1">
              <div className="p-3.5 rounded-2xl bg-white border border-[#E2E1DC]">
                <span className="text-[10px] font-bold text-[#434346] uppercase tracking-wider">Attack Vector Role</span>
                <p className="font-extrabold text-[#111312] mt-0.5">{currentStep.risk}</p>
                <p className="text-[11px] text-[#434346] mt-0.5">Function within campaign funnel</p>
              </div>

              <div className="p-3.5 rounded-2xl bg-white border border-[#E2E1DC]">
                <span className="text-[10px] font-bold text-[#434346] uppercase tracking-wider">Target Platform</span>
                <p className="font-extrabold text-[#111312] mt-0.5">{currentStep.platform}</p>
                <p className="text-[11px] text-[#434346] mt-0.5">Victim engagement surface</p>
              </div>

              <div className="p-3.5 rounded-2xl bg-white border border-[#E2E1DC]">
                <span className="text-[10px] font-bold text-[#434346] uppercase tracking-wider">Technical Evidence (IOC)</span>
                <p className="font-mono font-bold text-[#111312] mt-0.5 truncate">{currentStep.entity}</p>
                <p className="text-[11px] text-[#434346] mt-0.5">Identified forensic evidence</p>
              </div>
            </div>
          </div>

        </div>
      </Card>

      {/* ================= 5. STRUCTURED THREAT EVIDENCE & LINKED INDICATORS ================= */}
      <Card
        header={
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-[#111312]" />
                <h3 className="text-base font-extrabold text-[#111312]">Threat Evidence & Linked Items</h3>
              </div>
              <p className="text-xs text-[#434346] mt-0.5">
                Verified technical evidence linked to this campaign, including fake websites, social handles, and apps.
              </p>
            </div>

            <button
              onClick={() => setShowGlossary(!showGlossary)}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-[#111312] bg-[#FBF5A5] px-3 py-1.5 rounded-xl border border-[#DCDAD4] shrink-0 hover:bg-[#F3ED92] transition-colors"
            >
              <HelpCircle className="w-3.5 h-3.5 text-[#111312]" />
              <span>{showGlossary ? 'Hide Simple Explanations' : 'Plain-English Threat Explanations'}</span>
            </button>
          </div>
        }
      >
        <div className="space-y-5 pt-2">
          
          {/* Plain-English Technical Glossary Helper (Collapsible) */}
          {showGlossary && (
            <div className="p-4 rounded-2xl bg-[#F4F3EF] border border-[#DCDAD4] space-y-3 animate-in fade-in duration-200">
              <span className="text-[10px] font-black text-[#111312] uppercase tracking-wider block">
                Executive Cybersecurity Primer &mdash; Non-Jargon Explanations
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-white border border-[#E2E1DC]">
                  <strong className="text-[#111312] block">What is Technical Evidence (IOC / Hash)?</strong>
                  <span className="text-[#434346] text-[11px] mt-0.5 block">
                    A digital fingerprint (such as a lookalike web domain, IP address, or app file code) that security systems use to positively identify unauthorized fraudulent activity.
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-white border border-[#E2E1DC]">
                  <strong className="text-[#111312] block">What is a Control Server (C2)?</strong>
                  <span className="text-[#434346] text-[11px] mt-0.5 block">
                    A remote server operated by scammers to stealthily harvest login credentials entered by victims.
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-white border border-[#E2E1DC]">
                  <strong className="text-[#111312] block">What is a Fake App (Trojan APK)?</strong>
                  <span className="text-[#434346] text-[11px] mt-0.5 block">
                    A fraudulent Android app pretending to be an official bank utility, designed to steal customer passwords and SMS codes.
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-white border border-[#E2E1DC]">
                  <strong className="text-[#111312] block">What is a Lookalike Website (Typosquatting)?</strong>
                  <span className="text-[#434346] text-[11px] mt-0.5 block">
                    A deceptive domain name with slight misspellings or extra letters (like "apexbaank.com") designed to fool users who misspell your official web address.
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Evidence Category Filter Tabs */}
          <div className="flex flex-wrap items-center gap-2 border-b border-[#E2E1DC] pb-3">
            {[
              { id: 'all', label: `All Evidence (${evidenceItems.length})` },
              { id: 'web', label: 'Web & Domains (1)' },
              { id: 'social', label: 'Social Accounts (1)' },
              { id: 'apk', label: 'Rogue APKs (1)' },
              { id: 'c2', label: 'C2 Infrastructure (1)' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setEvidenceFilter(tab.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  evidenceFilter === tab.id
                    ? 'bg-[#111312] text-[#FBF5A5]'
                    : 'bg-white border border-[#E2E1DC] text-[#434346] hover:text-[#111312]'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Evidence Items List */}
          <div className="space-y-3">
            {filteredEvidence.map((item) => (
              <div 
                key={item.id}
                className="p-4 rounded-2xl bg-white border border-[#E2E1DC] hover:border-[#111312]/40 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div className="space-y-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[10px] font-bold text-[#111312] bg-[#F4F3EF] px-2.5 py-0.5 rounded-lg border border-[#DCDAD4] uppercase">
                      {item.type}
                    </span>
                    <span className="text-xs font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
                      Risk Score: {item.riskScore}/100
                    </span>
                    <span className="text-[11px] text-[#434346]">
                      Confidence: {item.confidence}%
                    </span>
                  </div>

                  <p className="font-mono text-xs font-extrabold text-[#111312] truncate">
                    {item.entity}
                  </p>

                  <p className="text-[11px] text-[#434346] leading-relaxed">
                    {item.plainDesc}
                  </p>
                </div>

                <div className="shrink-0 flex items-center gap-3">
                  <div className="text-right hidden sm:block">
                    <span className="text-[10px] font-bold text-[#434346] block">Status</span>
                    <span className="text-xs font-semibold text-[#111312]">{item.status}</span>
                  </div>

                  <Link to={`/brand-owner/threats/${item.threatId}`}>
                    <Button variant="outline" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                      Details
                    </Button>
                  </Link>
                </div>
              </div>
            ))}
          </div>

        </div>
      </Card>

      {/* ================= 6. TIMELINE & AFFECTED INFRASTRUCTURE ================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left: Campaign Activity Timeline */}
        <div className="lg:col-span-6">
          <Card
            header={
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-[#111312]" />
                <h3 className="text-base font-extrabold text-[#111312]">Campaign Activity Timeline</h3>
              </div>
            }
          >
            <div className="space-y-5 pt-2 pl-2">
              <div className="flex items-start gap-3 relative pl-5 border-l-2 border-[#111312]">
                <div className="w-2.5 h-2.5 rounded-full bg-[#111312] absolute -left-[6px] top-1.5 ring-4 ring-[#F4F3EF]" />
                <div>
                  <span className="text-[10px] font-bold text-[#434346]">Oct 6, 2026 &bull; Initial Detection</span>
                  <h5 className="text-xs font-bold text-[#111312]">Automated Crawler Flagged Typosquatted Domain</h5>
                  <p className="text-xs text-[#434346] mt-0.5 leading-relaxed">
                    BrandShield AI scanner picked up newly registered hostname imitating ApexBank branding.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 relative pl-5 border-l-2 border-amber-500">
                <div className="w-2.5 h-2.5 rounded-full bg-amber-500 absolute -left-[6px] top-1.5 ring-4 ring-[#F4F3EF]" />
                <div>
                  <span className="text-[10px] font-bold text-[#434346]">Oct 8, 2026 &bull; Multi-Vector Escalation</span>
                  <h5 className="text-xs font-bold text-[#111312]">Social Media Impersonation Bots Deployed</h5>
                  <p className="text-xs text-[#434346] mt-0.5 leading-relaxed">
                    Automated botnet swarm began replying to legitimate customer inquiries on Twitter with scam URLs.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 relative pl-5 border-l-2 border-rose-500">
                <div className="w-2.5 h-2.5 rounded-full bg-rose-500 absolute -left-[6px] top-1.5 ring-4 ring-[#F4F3EF]" />
                <div>
                  <span className="text-[10px] font-bold text-[#434346]">Oct 9, 2026 &bull; Malware Discovery</span>
                  <h5 className="text-xs font-bold text-[#111312]">Trojanized APK Package Detected</h5>
                  <p className="text-xs text-[#434346] mt-0.5 leading-relaxed">
                    Landing page began delivering malicious Android app sideloads designed to intercept SMS 2FA.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 relative pl-5 border-l-2 border-emerald-500">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 absolute -left-[6px] top-1.5 ring-4 ring-[#F4F3EF]" />
                <div>
                  <span className="text-[10px] font-bold text-emerald-700">Today &bull; Active Containment</span>
                  <h5 className="text-xs font-bold text-[#111312]">Coordinated Takedown Package Dispatched</h5>
                  <p className="text-xs text-[#434346] mt-0.5 leading-relaxed">
                    Abuse notices submitted to NameCheap, Cloudflare, and social network Trust & Safety desks.
                  </p>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Right: Affected Platforms & Jurisdictions */}
        <div className="lg:col-span-6">
          <Card
            header={
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-[#111312]" />
                <h3 className="text-base font-extrabold text-[#111312]">Platforms, Jurisdictions & Hosting</h3>
              </div>
            }
          >
            <div className="space-y-3 pt-1">
              <div className="p-3.5 rounded-2xl bg-[#F8F7F4] border border-[#E2E1DC] space-y-1">
                <span className="text-[10px] font-bold text-[#434346] uppercase tracking-wider block">Targeted Jurisdictions</span>
                <p className="text-xs font-bold text-[#111312]">{selectedCampaign.targetedRegions.join(' • ')}</p>
                <p className="text-[11px] text-[#434346]">Regional targets identified through localized lure phrasing and telephone country codes.</p>
              </div>

              <div className="p-3.5 rounded-2xl bg-[#F8F7F4] border border-[#E2E1DC] space-y-1">
                <span className="text-[10px] font-bold text-[#434346] uppercase tracking-wider block">Hosting Infrastructure</span>
                <p className="text-xs font-bold text-[#111312]">HostWinds Bulletproof VPS & DigitalOcean Amsterdam (ASN 14061)</p>
                <p className="text-[11px] text-[#434346]">Attacker employs offshore proxy nodes and Let's Encrypt certificates to evade detection.</p>
              </div>

              <div className="p-3.5 rounded-2xl bg-[#F8F7F4] border border-[#E2E1DC] space-y-1">
                <span className="text-[10px] font-bold text-[#434346] uppercase tracking-wider block">Recommended High-Level Response</span>
                <p className="text-xs font-bold text-[#111312]">Registrar Revocation + Mobile App Push Advisory + DNS Sinkhole</p>
                <p className="text-[11px] text-[#434346]">BrandShield AI takedown engine coordinates with both registrars and major browser vendors.</p>
              </div>
            </div>
          </Card>
        </div>

      </div>

      {/* ================= 7. PRIORITIZED RECOMMENDED ACTION PLAN ================= */}
      <div id="action-plan" className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-[#111312]" />
              <h2 className="text-lg font-black text-[#111312]">Prioritized Recommended Action Plan</h2>
            </div>
            <p className="text-xs text-[#434346] mt-0.5">
              Action items organized by urgency tier to rapidly neutralize the threat and protect customer accounts.
            </p>
          </div>
          <span className="text-xs font-bold text-[#111312] bg-[#FBF5A5] px-3 py-1.5 rounded-xl border border-[#DCDAD4]">
            3-Tier Remediation Framework
          </span>
        </div>

        <div className="space-y-4">
          
          {/* TIER 1: IMMEDIATE ACTIONS (< 1 HR) */}
          <div className="p-5 rounded-3xl bg-white border border-[#E2E1DC] shadow-soft space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E1DC]">
              <div className="flex items-center gap-2.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-600 animate-pulse" />
                <h3 className="text-sm font-black text-[#111312] uppercase tracking-wide">
                  Tier 1: Immediate Actions (&lt; 1 Hour)
                </h3>
              </div>
              <span className="text-[10px] font-bold text-rose-700 bg-rose-50 px-2.5 py-0.5 rounded-full border border-rose-200">
                Critical Urgency
              </span>
            </div>

            <div className="space-y-3">
              <div className="p-4 rounded-2xl bg-[#F8F7F4] border border-[#E2E1DC] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-extrabold text-[#111312]">Fast-Track Registrar Domain Takedown</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {actionStatuses.act_1}
                    </span>
                  </div>
                  <p className="text-xs text-[#434346]">
                    Submit automated DMCA & phishing revocation packet to NameCheap Abuse Desk for `apex-bank-secure-login.net`.
                  </p>
                  <p className="text-[11px] text-[#434346] font-semibold">
                    Expected Outcome: Domain DNS suspended within 4-6 hours.
                  </p>
                </div>

                <Button 
                  size="sm" 
                  variant={actionStatuses.act_1 === 'Dispatched' ? 'outline' : 'primary'}
                  disabled={actionStatuses.act_1 === 'Dispatched'}
                  onClick={() => handleExecuteAction('act_1', 'Fast-Track Registrar Domain Takedown')}
                >
                  {actionStatuses.act_1 === 'Dispatched' ? 'Dispatched' : 'Execute Takedown'}
                </Button>
              </div>

              <div className="p-4 rounded-2xl bg-[#F8F7F4] border border-[#E2E1DC] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-extrabold text-[#111312]">Social Impersonation Handle Suspension</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                      {actionStatuses.act_2}
                    </span>
                  </div>
                  <p className="text-xs text-[#434346]">
                    Dispatch urgent brand impersonation notice to X & Instagram Trust & Safety teams to terminate `@ApexBankHelp_Official`.
                  </p>
                  <p className="text-[11px] text-[#434346] font-semibold">
                    Expected Outcome: Social account suspended, preventing further customer DMs.
                  </p>
                </div>

                <Button 
                  size="sm"
                  variant={actionStatuses.act_2 === 'Dispatched' ? 'outline' : 'primary'}
                  disabled={actionStatuses.act_2 === 'Dispatched'}
                  onClick={() => handleExecuteAction('act_2', 'Social Impersonation Handle Suspension')}
                >
                  {actionStatuses.act_2 === 'Dispatched' ? 'Dispatched' : 'Submit Abuse Notice'}
                </Button>
              </div>
            </div>
          </div>

          {/* TIER 2: SHORT-TERM CONTAINMENT (< 24 HRS) */}
          <div className="p-5 rounded-3xl bg-white border border-[#E2E1DC] shadow-soft space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E1DC]">
              <div className="flex items-center gap-2.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                <h3 className="text-sm font-black text-[#111312] uppercase tracking-wide">
                  Tier 2: Short-Term Containment (&lt; 24 Hours)
                </h3>
              </div>
              <span className="text-[10px] font-bold text-amber-800 bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200">
                High Priority
              </span>
            </div>

            <div className="space-y-3">
              <div className="p-4 rounded-2xl bg-[#F8F7F4] border border-[#E2E1DC] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-extrabold text-[#111312]">Customer In-App Security Advisory</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                      {actionStatuses.act_3}
                    </span>
                  </div>
                  <p className="text-xs text-[#434346]">
                    Broadcast banner notification on official mobile banking app: "ApexBank will never ask for your 2FA passcode over SMS or Twitter."
                  </p>
                  <p className="text-[11px] text-[#434346] font-semibold">
                    Target: ~1,400 customers in affected regions.
                  </p>
                </div>

                <Button 
                  size="sm"
                  variant={actionStatuses.act_3 === 'Dispatched' ? 'outline' : 'primary'}
                  disabled={actionStatuses.act_3 === 'Dispatched'}
                  onClick={() => handleExecuteAction('act_3', 'Customer In-App Security Advisory')}
                >
                  {actionStatuses.act_3 === 'Dispatched' ? 'Broadcasted' : 'Broadcast Advisory'}
                </Button>
              </div>

              <div className="p-4 rounded-2xl bg-[#F8F7F4] border border-[#E2E1DC] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-extrabold text-[#111312]">Browser Threat Intelligence Feed Push</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                      {actionStatuses.act_4}
                    </span>
                  </div>
                  <p className="text-xs text-[#434346]">
                    Submit domain and IP indicators to Google Safe Browsing and Microsoft SmartScreen to trigger red warning interstitials.
                  </p>
                  <p className="text-[11px] text-[#434346] font-semibold">
                    Expected Outcome: 98% of browser traffic blocked automatically.
                  </p>
                </div>

                <Button 
                  size="sm"
                  variant={actionStatuses.act_4 === 'Dispatched' ? 'outline' : 'primary'}
                  disabled={actionStatuses.act_4 === 'Dispatched'}
                  onClick={() => handleExecuteAction('act_4', 'Browser Threat Feed Submission')}
                >
                  {actionStatuses.act_4 === 'Dispatched' ? 'Submitted' : 'Submit to Feeds'}
                </Button>
              </div>
            </div>
          </div>

          {/* TIER 3: ONGOING MONITORING */}
          <div className="p-5 rounded-3xl bg-white border border-[#E2E1DC] shadow-soft space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E1DC]">
              <div className="flex items-center gap-2.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#111312]" />
                <h3 className="text-sm font-black text-[#111312] uppercase tracking-wide">
                  Tier 3: Continuous Monitoring & Telemetry
                </h3>
              </div>
              <span className="text-[10px] font-bold text-[#111312] bg-[#F4F3EF] px-2.5 py-0.5 rounded-full border border-[#DCDAD4]">
                Proactive Defense
              </span>
            </div>

            <div className="space-y-3">
              <div className="p-4 rounded-2xl bg-[#F8F7F4] border border-[#E2E1DC] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-extrabold text-[#111312]">Typosquat Permutation Radar</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                      Active
                    </span>
                  </div>
                  <p className="text-xs text-[#434346]">
                    Continuous 24/7 scanning of 500+ newly registered DNS variations (e.g. `apexbank-login`, `apex-secure-verify`).
                  </p>
                </div>

                <Link to="/brand-owner/suspicious-websites">
                  <Button size="sm" variant="outline" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                    View Radar
                  </Button>
                </Link>
              </div>

              <div className="p-4 rounded-2xl bg-[#F8F7F4] border border-[#E2E1DC] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-extrabold text-[#111312]">Mobile App Store Package Hash Telemetry</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                      Active
                    </span>
                  </div>
                  <p className="text-xs text-[#434346]">
                    Automated APK signatures and package hash scanning across alternative third-party Android repositories.
                  </p>
                </div>

                <Link to="/brand-owner/suspicious-apps">
                  <Button size="sm" variant="outline" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                    View App Scanner
                  </Button>
                </Link>
              </div>
            </div>
          </div>

        </div>
      </div>

    </div>
  );
};
