import React, { useState } from 'react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { useNotification } from '../../context/NotificationContext';
import { 
  Users2, 
  Send, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  ExternalLink,
  Share2,
  MessageSquare,
  ShieldAlert
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const ImpersonationPage: React.FC = () => {
  const { showToast } = useNotification();

  const impersonators = [
    {
      id: 'imp_1',
      platform: 'Twitter / X',
      handle: '@ApexBankSupport_Help',
      url: 'https://twitter.com/ApexBankSupport_Help',
      avatarUrl: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=60&auto=format&fit=crop&q=80',
      followers: 14,
      targetType: 'Customer Support Bot',
      riskScore: 88,
      severity: 'high' as const,
      status: 'takedown_requested',
      detectedAt: 'Yesterday, 16:45',
      tactic: 'Replies to users with fake direct message links requesting 2FA seeds.'
    },
    {
      id: 'imp_2',
      platform: 'Telegram',
      handle: '@ApexBank_VIP_Investment_Bot',
      url: 'https://t.me/ApexBank_VIP_Investment_Bot',
      avatarUrl: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=60&auto=format&fit=crop&q=80',
      followers: 1200,
      targetType: 'Fake Investment Scheme',
      riskScore: 94,
      severity: 'critical' as const,
      status: 'active',
      detectedAt: '2 days ago',
      tactic: 'Promising 20% daily compounding returns using unauthorized ApexBank logos.'
    },
    {
      id: 'imp_3',
      platform: 'LinkedIn',
      handle: 'Marcus Vance (Apex Senior Loan Officer)',
      url: 'https://linkedin.com/in/fake-marcus-apex',
      avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=60&auto=format&fit=crop&q=80',
      followers: 88,
      targetType: 'Executive Impersonation',
      riskScore: 76,
      severity: 'medium' as const,
      status: 'under_investigation',
      detectedAt: '3 days ago',
      tactic: 'Soliciting upfront loan processing fees from small business owners.'
    },
    {
      id: 'imp_4',
      platform: 'Instagram',
      handle: '@apexbank_giveaway_official',
      url: 'https://instagram.com/apexbank_giveaway_official',
      avatarUrl: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=60&auto=format&fit=crop&q=80',
      followers: 430,
      targetType: 'Fake Contest / Giveaway',
      riskScore: 65,
      severity: 'medium' as const,
      status: 'resolved',
      detectedAt: '5 days ago',
      tactic: 'Account suspended following Meta Brand Protection API submission.'
    }
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-brand-dark tracking-tight">Social & Executive Impersonation</h1>
          <p className="text-xs text-brand-muted mt-1">
            Detect and dismantle fake customer care accounts, scam investment bots, and unauthorized employee profiles.
          </p>
        </div>

        <div className="p-2.5 rounded-2xl bg-[#111312] border border-[#2B2D2C] text-xs font-bold text-[#FBF5A5] flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-[#FBF5A5]" />
          <span>Social Threat Feeds Syncing (X, Telegram, Meta, Discord)</span>
        </div>
      </div>

      {/* Impersonator Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {impersonators.map((imp) => (
          <Card key={imp.id} className="space-y-4">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <img
                  src={imp.avatarUrl}
                  alt={imp.handle}
                  className="w-12 h-12 rounded-2xl object-cover border border-brand-border shadow-sm shrink-0"
                />
                <div>
                  <span className="text-[10px] font-bold text-[#111312] uppercase">{imp.platform} &bull; {imp.targetType}</span>
                  <h3 className="text-sm font-extrabold text-brand-dark truncate">{imp.handle}</h3>
                  <p className="text-[11px] text-brand-muted">{imp.followers} followers &bull; Detected {imp.detectedAt}</p>
                </div>
              </div>

              <Badge severity={imp.severity} size="sm" />
            </div>

            <div className="p-3 rounded-2xl bg-brand-surface-light border border-brand-border text-xs space-y-1">
              <span className="text-[10px] font-bold text-brand-muted uppercase">Detected Tactic:</span>
              <p className="text-brand-dark leading-relaxed">{imp.tactic}</p>
            </div>

            <div className="pt-3 border-t border-brand-border/60 flex items-center justify-between">
              <Badge status={imp.status} size="sm" />

              <Link to="/brand-owner/threats/threat_apex_03">
                <Button variant="secondary" size="sm" rightIcon={<ExternalLink className="w-3.5 h-3.5" />}>
                  Inspect Evidence
                </Button>
              </Link>
            </div>
          </Card>
        ))}
      </div>

    </div>
  );
};
