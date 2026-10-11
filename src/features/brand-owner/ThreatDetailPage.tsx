import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useBrand } from '../../context/BrandContext';
import { threatService } from '../../services/api';
import { SuspiciousThreat, ThreatStatus } from '../../types';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { RiskGauge } from '../../components/ui/RiskGauge';
import { useNotification } from '../../context/NotificationContext';
import { 
  ArrowLeft, 
  ShieldAlert, 
  Send, 
  CheckCircle2, 
  Clock, 
  FileText, 
  ExternalLink, 
  Server, 
  Globe2, 
  AlertTriangle, 
  Lock, 
  Eye, 
  Sparkles, 
  Copy, 
  Check, 
  MessageSquare,
  ShieldCheck,
  FileDown,
  ChevronDown,
  ChevronUp,
  AlertOctagon,
  Users2,
  Lightbulb
} from 'lucide-react';
import confetti from 'canvas-confetti';

interface FormattedNote {
  timestamp: string;
  category: string;
  source: string;
  text: string;
  icon: React.ComponentType<{ className?: string }>;
  badgeStyle: string;
  borderAccent: string;
}

const parseNote = (rawNote: string): FormattedNote => {
  let text = rawNote.trim();
  let timestamp = '';

  // 1. Check for leading timestamp like [11:41:54 AM] or [10:15:00 AM]
  const timeMatch = text.match(/^\[(.*?)\]\s*/);
  if (timeMatch) {
    timestamp = timeMatch[1];
    text = text.replace(/^\[(.*?)\]\s*/, '').trim();
  }

  // 2. Check for "Status changed to <status>: <details>"
  if (text.toLowerCase().includes('status changed to')) {
    const statusMatch = text.match(/status changed to ([^:]+):?\s*(.*)/i);
    const statusName = statusMatch ? statusMatch[1].replace(/_/g, ' ').toUpperCase() : 'STATUS EVENT';
    const detail = statusMatch && statusMatch[2] ? statusMatch[2] : text;
    return {
      timestamp: timestamp || 'Just now',
      category: `Status: ${statusName}`,
      source: 'Threat Management Console',
      text: detail,
      icon: ShieldAlert,
      badgeStyle: 'bg-rose-50 text-rose-700 border-rose-200',
      borderAccent: 'border-l-rose-500'
    };
  }

  // 3. Check for "Analyst Note: <details>"
  if (text.toLowerCase().startsWith('analyst note:')) {
    const cleanText = text.replace(/^analyst note:\s*/i, '').trim();
    return {
      timestamp: timestamp || 'Logged Note',
      category: 'Analyst Observation',
      source: 'Security Analyst',
      text: cleanText,
      icon: MessageSquare,
      badgeStyle: 'bg-[#FBF5A5] text-[#111312] border-[#DCDAD4] font-bold',
      borderAccent: 'border-l-[#111312]'
    };
  }

  // 4. Check for crawler / telemetry
  if (text.toLowerCase().includes('crawler') || text.toLowerCase().includes('http post') || text.toLowerCase().includes('endpoint')) {
    return {
      timestamp: timestamp || 'Telemetry Signal',
      category: 'Detection Telemetry',
      source: 'Automated Crawler Engine',
      text: text,
      icon: Globe2,
      badgeStyle: 'bg-sky-50 text-sky-700 border-sky-200',
      borderAccent: 'border-l-sky-500'
    };
  }

  // 5. Check for SSL cert
  if (text.toLowerCase().includes('ssl') || text.toLowerCase().includes('cert') || text.toLowerCase().includes("let's encrypt")) {
    return {
      timestamp: timestamp || '18h ago',
      category: 'Certificate Intel',
      source: 'Certificate Transparency Log',
      text: text,
      icon: Lock,
      badgeStyle: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      borderAccent: 'border-l-emerald-500'
    };
  }

  // 6. Check for takedown / abuse desk
  if (text.toLowerCase().includes('takedown') || text.toLowerCase().includes('abuse desk') || text.toLowerCase().includes('namecheap')) {
    return {
      timestamp: timestamp || 'SOC Action',
      category: 'Abuse Desk Notice',
      source: 'BrandShield SOC Team',
      text: text,
      icon: Send,
      badgeStyle: 'bg-[#111312] text-[#FBF5A5] border-[#2B2D2C]',
      borderAccent: 'border-l-[#111312]'
    };
  }

  // 7. Fallback generic note
  return {
    timestamp: timestamp || 'Logged Note',
    category: 'Analyst Log',
    source: 'Investigation Team',
    text: text,
    icon: FileText,
    badgeStyle: 'bg-[#F4F3EF] text-[#434346] border-[#DCDAD4]',
    borderAccent: 'border-l-[#434346]'
  };
};

export const ThreatDetailPage: React.FC = () => {
  const { threatId } = useParams<{ threatId?: string }>();
  const { currentBrand } = useBrand();
  const navigate = useNavigate();
  const { showToast } = useNotification();

  const [allThreats, setAllThreats] = useState<SuspiciousThreat[]>([]);
  const [threat, setThreat] = useState<SuspiciousThreat | null>(null);
  const [newAnalystNote, setNewAnalystNote] = useState('');
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [copiedUrl, setCopiedUrl] = useState(false);

  useEffect(() => {
    const loadThreatData = async () => {
      setIsLoading(true);
      try {
        if (currentBrand) {
          const list = await threatService.getThreats(currentBrand.id);
          setAllThreats(list);

          const target = threatId 
            ? list.find(t => t.id === threatId) || list[0]
            : list[0];

          setThreat(target || null);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    loadThreatData();
  }, [threatId, currentBrand]);

  if (isLoading || !threat) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="w-10 h-10 border-3 border-[#111312] border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-brand-muted">Loading threat investigation details...</p>
      </div>
    );
  }

  const handleStatusChange = async (newStatus: ThreatStatus) => {
    setIsUpdatingStatus(true);
    try {
      const updated = await threatService.updateThreatStatus(
        threat.id, 
        newStatus, 
        `Status updated via Threat Details Console to ${newStatus}`
      );
      setThreat(updated);
      
      if (newStatus === 'takedown_requested') {
        confetti({ particleCount: 60, spread: 50 });
        showToast({ 
          type: 'success', 
          title: 'Takedown Dispatched!', 
          message: `Abuse package sent to ${updated.takedownStatus?.authorityContacted || 'registrar abuse desk'}.` 
        });
      } else {
        showToast({ type: 'success', title: 'Status Updated', message: `Threat is now marked as ${newStatus}.` });
      }
    } catch (err: any) {
      showToast({ type: 'error', title: 'Update Failed', message: err.message });
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAnalystNote.trim()) return;

    try {
      const updated = await threatService.addAnalystNote(threat.id, newAnalystNote);
      setThreat(updated);
      setNewAnalystNote('');
      showToast({ type: 'success', title: 'Note Added', message: 'Observation logged to threat record.' });
    } catch (err) {
      showToast({ type: 'error', title: 'Failed to add note', message: 'Please try again.' });
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedUrl(true);
    showToast({ type: 'success', title: 'Copied', message: 'Target URL copied to clipboard.' });
    setTimeout(() => setCopiedUrl(false), 2000);
  };

  const handleExportPDF = () => {
    showToast({ 
      type: 'info', 
      title: 'Generating PDF Dossier', 
      message: `Executive threat report for ${threat.targetDomainOrUrl} prepared for printing.` 
    });
    window.print();
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Top Navigation & Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/brand-owner/threat-management"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-muted hover:text-[#111312] transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Threat Management</span>
          </Link>

          {/* Quick Threat Switcher */}
          {allThreats.length > 1 && (
            <select
              value={threat.id}
              onChange={(e) => {
                const selected = allThreats.find(t => t.id === e.target.value);
                if (selected) setThreat(selected);
              }}
              className="px-3 py-1.5 text-xs font-bold rounded-xl bg-brand-surface-light border border-brand-border text-brand-dark focus:outline-none focus:border-[#111312] max-w-[200px] truncate"
            >
              {allThreats.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.targetDomainOrUrl}
                </option>
              ))}
            </select>
          )}
        </div>

        <div className="flex items-center gap-3">
          <Link to={`/brand-owner/ai-threat-explanation?threatId=${threat.id}`}>
            <Button variant="outline" size="sm" leftIcon={<Sparkles className="w-4 h-4" />}>
              AI Explanation
            </Button>
          </Link>

          <Link to={`/brand-owner/recommended-actions?threatId=${threat.id}`}>
            <Button variant="outline" size="sm" leftIcon={<Lightbulb className="w-4 h-4" />}>
              Recommended Actions
            </Button>
          </Link>

          <Button
            variant="outline"
            size="sm"
            onClick={handleExportPDF}
            leftIcon={<FileDown className="w-4 h-4" />}
          >
            Export Dossier
          </Button>

          {threat.status !== 'takedown_requested' && threat.status !== 'resolved' && (
            <Button
              size="sm"
              onClick={() => handleStatusChange('takedown_requested')}
              isLoading={isUpdatingStatus}
              leftIcon={<Send className="w-4 h-4" />}
            >
              Request Takedown
            </Button>
          )}
        </div>
      </div>

      {/* Main Threat Overview Banner */}
      <div className="p-6 rounded-3xl bg-white border border-brand-border shadow-soft space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] font-bold text-brand-muted uppercase tracking-wider">Identified Impersonation Target</span>
              <Badge severity={threat.severity} size="sm" />
              <Badge status={threat.status} size="sm" />
            </div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-mono font-extrabold text-brand-dark">
                {threat.targetDomainOrUrl}
              </h1>
              <button
                onClick={() => handleCopy(threat.targetDomainOrUrl)}
                className="p-1 rounded-lg text-brand-muted hover:text-[#111312] hover:bg-[#F4F3EF]"
                title="Copy URL"
              >
                {copiedUrl ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-xs text-brand-muted mt-1">
              First detected on <strong className="text-brand-dark">{new Date(threat.firstSeenAt).toLocaleString()}</strong> via <strong className="text-[#111312]">{threat.source.replace(/_/g, ' ')}</strong>
            </p>
          </div>

          {/* Potential Impact Callout */}
          <div className="p-4 rounded-2xl bg-rose-50/80 border border-rose-200 text-xs space-y-1 shrink-0 max-w-sm">
            <span className="text-[10px] font-bold text-rose-800 uppercase tracking-wider flex items-center gap-1">
              <AlertOctagon className="w-3.5 h-3.5 text-rose-600" /> Estimated Potential Impact
            </span>
            <p className="font-bold text-rose-950">
              ~{threat.reportedByCount * 120 + 350} Customers at Risk of Credential Theft
            </p>
            <p className="text-[11px] text-rose-800">
              Active credential harvesting targeting customer banking credentials and 2FA tokens.
            </p>
          </div>
        </div>
      </div>

      {/* Main Grid: Details + Business Plain English Explanation */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Plain English Why Flagged + Visual Evidence Preview (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* Plain English Business Explanation */}
          <Card
            header={
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-[#111312]" />
                <h3 className="text-sm font-bold text-brand-dark">Why This Threat Was Flagged (Simple Explanation)</h3>
              </div>
            }
          >
            <div className="space-y-4 text-xs">
              <div className="p-4 rounded-2xl bg-brand-surface-light border border-brand-border space-y-2">
                <p className="font-bold text-brand-dark text-sm leading-snug">
                  {threat.riskExplanation}
                </p>
                <p className="text-brand-muted leading-relaxed">
                  Our automated brand defense engine detected that this unauthorized domain copies your official brand identity, logo, and page styling to deceive your customers into submitting sensitive login information.
                </p>
              </div>

              {/* Key Indicators in Plain English */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3.5 rounded-2xl bg-white border border-brand-border space-y-1">
                  <span className="text-[10px] font-bold text-brand-muted uppercase">Visual Copying</span>
                  <p className="text-lg font-extrabold text-rose-600">{threat.visualSimilarityScore}% Match</p>
                  <p className="text-[10px] text-brand-muted">Copies official site colors and layout</p>
                </div>

                <div className="p-3.5 rounded-2xl bg-white border border-brand-border space-y-1">
                  <span className="text-[10px] font-bold text-brand-muted uppercase">Logo Impersonation</span>
                  <p className="text-lg font-extrabold text-rose-600">{threat.logoSimilarityScore}% Match</p>
                  <p className="text-[10px] text-brand-muted">Unauthorized trademark usage</p>
                </div>

                <div className="p-3.5 rounded-2xl bg-white border border-brand-border space-y-1">
                  <span className="text-[10px] font-bold text-brand-muted uppercase">Domain Lookalike</span>
                  <p className="text-lg font-extrabold text-amber-600">{threat.domainSimilarityScore}% Match</p>
                  <p className="text-[10px] text-brand-muted">Typosquatting deceptive domain name</p>
                </div>
              </div>
            </div>
          </Card>

          {/* Supporting Evidence Highlights */}
          <Card
            header={
              <div className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-[#111312]" />
                <h3 className="text-sm font-bold text-brand-dark">Supporting Evidence & Key Signals</h3>
              </div>
            }
          >
            <div className="space-y-3">
              {threat.evidence.length > 0 ? (
                threat.evidence.map((ev) => (
                  <div key={ev.id} className="p-4 rounded-2xl bg-brand-surface-light border border-brand-border space-y-1.5">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-brand-dark">{ev.title}</h4>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {ev.confidenceScore}% Confidence
                      </span>
                    </div>
                    <p className="text-xs text-brand-muted leading-relaxed">
                      {ev.description}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-xs text-brand-muted text-center py-4">Evidence verified by automated crawler.</p>
              )}
            </div>
          </Card>

        </div>

        {/* Right Column: Sticky, Elevated Risk & Status, and Fixed-Height Structured Investigation Notes */}
        <div className="lg:col-span-4 space-y-5 lg:sticky lg:top-6 lg:self-start">
          
          {/* Card 1: Risk Assessment & Investigation State (Compact & Unified) */}
          <Card className="p-5 space-y-4">
            <RiskGauge
              score={threat.riskScore}
              severity={threat.severity}
              confidence={threat.modelConfidence}
              modelVersion={threat.scoringVersion}
              explanation={threat.riskExplanation}
              size="md"
            />

            <div className="pt-3 border-t border-[#E2E1DC] space-y-2.5">
              <div className="flex items-center justify-between">
                <label className="text-[10px] font-black text-[#111312] uppercase tracking-wider">
                  Investigation Status
                </label>
                <Badge status={threat.status} size="sm" />
              </div>
              
              <select
                value={threat.status}
                onChange={(e) => handleStatusChange(e.target.value as ThreatStatus)}
                className="w-full rounded-xl bg-[#F8F7F4] border border-[#E2E1DC] px-3 py-2 text-xs font-bold text-[#111312] focus:outline-none focus:border-[#111312] shadow-xs"
              >
                <option value="active">Active Threat</option>
                <option value="under_investigation">Being reviewed</option>
                <option value="takedown_requested">Removal requested</option>
                <option value="resolved">Resolved / Removed</option>
                <option value="false_positive">Safe / Allowed</option>
              </select>

              {/* Takedown Status Details */}
              {threat.takedownStatus && (
                <div className="p-3 rounded-xl bg-[#F4F3EF] border border-[#DCDAD4] text-xs space-y-1">
                  <div className="flex items-center justify-between text-[#111312] font-bold">
                    <span>Abuse Ticket</span>
                    <span className="font-mono text-[11px]">{threat.takedownStatus.ticketId}</span>
                  </div>
                  <p className="text-[11px] text-[#434346]">
                    Authority: <strong className="text-[#111312]">{threat.takedownStatus.authorityContacted}</strong>
                  </p>
                  <p className="text-[11px] text-[#434346]">
                    Est. Resolution: <strong className="text-[#111312]">{threat.takedownStatus.estimatedResolution}</strong>
                  </p>
                </div>
              )}
            </div>
          </Card>

          {/* Card 2: Structured & Elevated Investigation Notes (Fixed Height, No Page Scroll) */}
          <Card
            header={
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-[#111312] text-[#FBF5A5]">
                    <MessageSquare className="w-3.5 h-3.5" />
                  </div>
                  <h3 className="text-sm font-extrabold text-[#111312]">Investigation Notes</h3>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-[10px] font-bold text-[#434346] bg-[#F4F3EF] px-2 py-0.5 rounded-full border border-[#DCDAD4]">
                    {threat.analystNotes?.length || 0} Recorded
                  </span>
                </div>
              </div>
            }
          >
            <div className="space-y-3 pt-1">
              {/* Form Input */}
              <form onSubmit={handleAddNote} className="flex gap-2">
                <input
                  type="text"
                  value={newAnalystNote}
                  onChange={(e) => setNewAnalystNote(e.target.value)}
                  placeholder="Add note or observation..."
                  className="flex-1 rounded-xl bg-[#F8F7F4] border border-[#E2E1DC] px-3 py-2 text-xs text-[#111312] focus:outline-none focus:border-[#111312] placeholder:text-[#434346]"
                />
                <Button type="submit" size="sm">
                  Add
                </Button>
              </form>

              {/* Fixed Height Scrollable Notes List (Never causes entire page to scroll) */}
              <div className="max-h-[300px] overflow-y-auto pr-1 space-y-2.5">
                {threat.analystNotes && threat.analystNotes.length > 0 ? (
                  threat.analystNotes.map((rawNote, idx) => {
                    const parsed = parseNote(rawNote);
                    const Icon = parsed.icon;

                    return (
                      <div 
                        key={idx} 
                        className={`p-3 rounded-2xl bg-white border border-[#E2E1DC] hover:border-[#111312]/30 transition-all space-y-1.5 border-l-4 ${parsed.borderAccent} shadow-xs`}
                      >
                        {/* Note Header: Category + Timestamp */}
                        <div className="flex items-center justify-between gap-2">
                          <span className={`text-[10px] font-black px-2 py-0.5 rounded-lg border flex items-center gap-1 ${parsed.badgeStyle}`}>
                            <Icon className="w-2.5 h-2.5 shrink-0" />
                            <span className="truncate">{parsed.category}</span>
                          </span>

                          <span className="text-[10px] font-semibold text-[#434346] shrink-0">
                            {parsed.timestamp}
                          </span>
                        </div>

                        {/* Note Body */}
                        <p className="text-xs font-semibold text-[#111312] leading-relaxed">
                          {parsed.text}
                        </p>

                        {/* Note Origin Footnote */}
                        <div className="flex items-center justify-between text-[10px] text-[#434346] pt-1 border-t border-[#E2E1DC]/60">
                          <span>Origin: <strong className="text-[#111312]">{parsed.source}</strong></span>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <p className="text-xs text-[#434346] text-center py-4">No notes recorded yet.</p>
                )}
              </div>
            </div>
          </Card>

        </div>

      </div>

    </div>
  );
};
