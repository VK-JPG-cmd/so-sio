import React, { useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useBrand } from '../../context/BrandContext';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { useNotification } from '../../context/NotificationContext';
import { 
  Lightbulb, 
  CheckCircle2, 
  Clock, 
  Send, 
  Globe2, 
  Users2, 
  Smartphone, 
  ShieldAlert, 
  Plus, 
  ArrowRight,
  AlertTriangle,
  FileText,
  Sparkles,
  ExternalLink,
  ShieldCheck
} from 'lucide-react';
import confetti from 'canvas-confetti';

interface ActionItem {
  id: string;
  title: string;
  threatTarget: string;
  category: 'takedown' | 'customer_warning' | 'social_report' | 'dns_block';
  description: string;
  status: 'suggested' | 'in_progress' | 'completed';
  urgency: 'critical' | 'high' | 'medium';
  completedAt?: string;
}

export const RecommendedActionsPage: React.FC = () => {
  const { currentBrand } = useBrand();
  const { showToast } = useNotification();
  const [searchParams] = useSearchParams();

  const [actions, setActions] = useState<ActionItem[]>([
    {
      id: 'act_1',
      title: 'Dispatch Fast-Track Registrar Abuse Complaint',
      threatTarget: 'apex-bank-secure-login.net/verify',
      category: 'takedown',
      description: 'Submit verified UDRP / fraud abuse notice to NameCheap & Cloudflare Trust & Safety to suspend the phishing domain.',
      status: 'suggested',
      urgency: 'critical'
    },
    {
      id: 'act_2',
      title: 'Issue In-App Customer Security Advisory',
      threatTarget: 'Operation "PhishVault 2026" Syndicate',
      category: 'customer_warning',
      description: 'Notify mobile banking users never to share 2FA OTP codes via SMS or click external password reset links.',
      status: 'suggested',
      urgency: 'high'
    },
    {
      id: 'act_3',
      title: 'Report Social Impersonator to X (Twitter) Trust & Safety',
      threatTarget: '@ApexBankSupport_Help',
      category: 'social_report',
      description: 'Submit VIP partner escalated takedown ticket to suspend the fraudulent support handle messaging customers.',
      status: 'in_progress',
      urgency: 'high'
    },
    {
      id: 'act_4',
      title: 'Add Typosquat Domain to Global DNS Sinkhole & Browser Blocklists',
      threatTarget: 'apexbaank.com',
      category: 'dns_block',
      description: 'Publish telemetry IOC to Google Safe Browsing and Microsoft SmartScreen to protect users attempting navigation.',
      status: 'completed',
      urgency: 'high',
      completedAt: '2 hours ago'
    },
    {
      id: 'act_5',
      title: 'Notify Webmaster of Compromised WordPress Host',
      threatTarget: 'apex-banking-portal-update.org',
      category: 'takedown',
      description: 'Sent abuse remediation package to site owner. Malicious sub-directory deleted and cleaned.',
      status: 'completed',
      urgency: 'medium',
      completedAt: 'Yesterday'
    }
  ]);

  const handleExecuteAction = (actionId: string, title: string) => {
    setActions(actions.map(a => a.id === actionId ? { ...a, status: 'in_progress' } : a));
    confetti({ particleCount: 50, spread: 45 });
    showToast({
      type: 'success',
      title: 'Action Initiated',
      message: `${title} is now in progress.`
    });
  };

  const handleCompleteAction = (actionId: string, title: string) => {
    setActions(actions.map(a => a.id === actionId ? { ...a, status: 'completed', completedAt: 'Just now' } : a));
    showToast({
      type: 'success',
      title: 'Action Completed',
      message: `${title} marked as successfully resolved.`
    });
  };

  const suggestedActions = actions.filter(a => a.status === 'suggested');
  const inProgressActions = actions.filter(a => a.status === 'in_progress');
  const completedActions = actions.filter(a => a.status === 'completed');

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-brand-dark tracking-tight">Recommended Actions</h1>
          <p className="text-xs text-brand-muted mt-1">
            Practical security playbooks and response plans tailored to each detected threat and scam campaign.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link to="/brand-owner/ai-threat-explanation">
            <Button variant="outline" size="sm" leftIcon={<Sparkles className="w-4 h-4" />}>
              AI Threat Explanation
            </Button>
          </Link>
          <Link to="/brand-owner/threat-management">
            <Button size="sm">
              Threat Workspace
            </Button>
          </Link>
        </div>
      </div>

      {/* Plan Status Counters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-2xl bg-amber-50/70 border border-amber-200">
          <span className="text-[10px] font-bold text-amber-800 uppercase tracking-wider block">Suggested Next Steps</span>
          <p className="text-2xl font-extrabold text-amber-900 mt-1">{suggestedActions.length} Pending Actions</p>
          <p className="text-[11px] text-amber-700 mt-1">High-impact actions awaiting approval</p>
        </div>

        <div className="p-4 rounded-2xl bg-blue-50/70 border border-blue-200">
          <span className="text-[10px] font-bold text-blue-800 uppercase tracking-wider block">In Progress</span>
          <p className="text-2xl font-extrabold text-blue-900 mt-1">{inProgressActions.length} Actions Active</p>
          <p className="text-[11px] text-blue-700 mt-1">Awaiting registrar / platform execution</p>
        </div>

        <div className="p-4 rounded-2xl bg-emerald-50/70 border border-emerald-200">
          <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider block">Completed Actions</span>
          <p className="text-2xl font-extrabold text-emerald-900 mt-1">{completedActions.length} Neutralized</p>
          <p className="text-[11px] text-emerald-700 mt-1">Successfully mitigated threats</p>
        </div>
      </div>

      {/* SECTION 1: Suggested Actions */}
      <Card
        header={
          <div className="flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-amber-600" />
            <div>
              <h3 className="text-sm font-bold text-brand-dark">Suggested Actions (Awaiting Your Trigger)</h3>
              <p className="text-xs text-brand-muted">AI-recommended playbooks tailored to mitigate active threats</p>
            </div>
          </div>
        }
      >
        <div className="space-y-4">
          {suggestedActions.length > 0 ? (
            suggestedActions.map((action) => (
              <div 
                key={action.id} 
                className="p-4 rounded-2xl bg-brand-surface-light border border-brand-border flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h4 className="text-xs font-bold text-brand-dark">{action.title}</h4>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      action.urgency === 'critical' ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-amber-50 text-amber-700 border border-amber-200'
                    }`}>
                      {action.urgency.toUpperCase()}
                    </span>
                    <span className="font-mono text-[11px] text-[#111312] font-bold bg-white px-2 py-0.5 rounded-md border border-brand-border truncate max-w-xs">
                      {action.threatTarget}
                    </span>
                  </div>
                  <p className="text-xs text-brand-muted leading-relaxed">
                    {action.description}
                  </p>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Button size="sm" onClick={() => handleExecuteAction(action.id, action.title)} leftIcon={<Send className="w-3.5 h-3.5" />}>
                    Execute Action
                  </Button>
                </div>
              </div>
            ))
          ) : (
            <p className="text-xs text-brand-muted text-center py-4">No pending suggested actions at this time.</p>
          )}
        </div>
      </Card>

      {/* SECTION 2: In-Progress Actions */}
      {inProgressActions.length > 0 && (
        <Card
          header={
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-600" />
              <div>
                <h3 className="text-sm font-bold text-brand-dark">In-Progress Actions</h3>
                <p className="text-xs text-brand-muted">Tickets and takedown packages currently being processed</p>
              </div>
            </div>
          }
        >
          <div className="space-y-3">
            {inProgressActions.map((action) => (
              <div 
                key={action.id} 
                className="p-4 rounded-2xl bg-blue-50/40 border border-blue-200/60 flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h4 className="text-xs font-bold text-brand-dark">{action.title}</h4>
                    <span className="font-mono text-[11px] text-[#111312] font-bold bg-white px-2 py-0.5 rounded-md border border-brand-border">
                      {action.threatTarget}
                    </span>
                  </div>
                  <p className="text-xs text-brand-muted leading-relaxed">
                    {action.description}
                  </p>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Button variant="outline" size="sm" onClick={() => handleCompleteAction(action.id, action.title)} leftIcon={<CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />}>
                    Mark as Completed
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* SECTION 3: Completed Actions */}
      <Card
        header={
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <div>
              <h3 className="text-sm font-bold text-brand-dark">Completed Actions & Resolution Log</h3>
              <p className="text-xs text-brand-muted">History of executed mitigations and resolved security tickets</p>
            </div>
          </div>
        }
      >
        <div className="space-y-3">
          {completedActions.map((action) => (
            <div 
              key={action.id} 
              className="p-4 rounded-2xl bg-emerald-50/40 border border-emerald-200/60 flex items-center justify-between gap-4"
            >
              <div className="space-y-0.5">
                <div className="flex items-center gap-2 flex-wrap">
                  <h4 className="text-xs font-bold text-brand-dark">{action.title}</h4>
                  <span className="font-mono text-[11px] text-brand-muted bg-white px-2 py-0.5 rounded-md border border-brand-border">
                    {action.threatTarget}
                  </span>
                </div>
                <p className="text-xs text-brand-muted">{action.description}</p>
              </div>

              <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100/70 px-2.5 py-1 rounded-full shrink-0">
                Completed {action.completedAt}
              </span>
            </div>
          ))}
        </div>
      </Card>

    </div>
  );
};
