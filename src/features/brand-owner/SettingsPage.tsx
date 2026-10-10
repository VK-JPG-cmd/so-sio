import React, { useState } from 'react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useNotification } from '../../context/NotificationContext';
import { 
  Key, 
  Webhook, 
  Users, 
  Bell, 
  ShieldCheck, 
  Copy, 
  Check, 
  RefreshCw,
  Sparkles
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { showToast } = useNotification();
  const [apiKey, setApiKey] = useState('bs_live_89f3a92147e098bc9128f731');
  const [webhookUrl, setWebhookUrl] = useState('https://hooks.slack.com/services/T00/B00/XXXXX');
  const [copied, setCopied] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const handleCopyKey = () => {
    navigator.clipboard.writeText(apiKey);
    setCopied(true);
    showToast({ type: 'success', title: 'API Key Copied', message: 'Ready to use in your CI/CD or SIEM pipelines.' });
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRegenerate = () => {
    const newKey = `bs_live_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`;
    setApiKey(newKey);
    showToast({ type: 'info', title: 'API Key Rotated', message: 'New API token created.' });
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      showToast({ type: 'success', title: 'Settings Saved', message: 'Integration preferences updated.' });
    }, 600);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Title */}
      <div>
        <h1 className="text-2xl font-extrabold text-brand-dark tracking-tight">Security Integrations & Settings</h1>
        <p className="text-xs text-brand-muted mt-1">
          Manage API keys for FastAPI backend integration, SIEM webhooks, and team access control.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* API Keys and Webhooks (8-cols) */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* API Key Management */}
          <Card
            header={
              <div className="flex items-center gap-2">
                <Key className="w-4 h-4 text-[#111312]" />
                <h3 className="text-sm font-bold text-brand-dark">BrandShield REST API Tokens</h3>
              </div>
            }
          >
            <div className="space-y-4">
              <p className="text-xs text-brand-muted">
                Use this secret key to authenticate backend ingestion endpoints and programmatic takedown dispatches.
              </p>

              <div className="flex items-center gap-2">
                <div className="flex-1 p-2.5 rounded-2xl bg-brand-surface-light border border-brand-border font-mono text-xs text-brand-dark truncate">
                  {apiKey}
                </div>
                <Button variant="outline" size="sm" onClick={handleCopyKey}>
                  {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                </Button>
                <Button variant="secondary" size="sm" onClick={handleRegenerate} leftIcon={<RefreshCw className="w-3.5 h-3.5" />}>
                  Rotate
                </Button>
              </div>
            </div>
          </Card>

          {/* Webhooks & Alerts Dispatch */}
          <Card
            header={
              <div className="flex items-center gap-2">
                <Webhook className="w-4 h-4 text-[#111312]" />
                <h3 className="text-sm font-bold text-brand-dark">SOC & Incident Webhooks</h3>
              </div>
            }
          >
            <form onSubmit={handleSave} className="space-y-4">
              <Input
                label="Slack / Discord / PagerDuty Incident Webhook URL"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
                placeholder="https://hooks.slack.com/services/..."
                helperText="BrandShield will dispatch JSON payloads for high & critical severity threats."
              />

              <div className="space-y-2 pt-2">
                <label className="block text-xs font-semibold text-brand-dark">Notification Triggers</label>
                <div className="space-y-2 text-xs text-brand-dark">
                  <label className="flex items-center gap-2">
                    <input type="checkbox" defaultChecked className="rounded border-brand-border text-[#111312] focus:ring-[#111312]" />
                    <span>Critical Severity Phishing URL detected</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" defaultChecked className="rounded border-brand-border text-[#111312] focus:ring-[#111312]" />
                    <span>Customer report receives &gt; 5 community confirmations</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" defaultChecked className="rounded border-brand-border text-[#111312] focus:ring-[#111312]" />
                    <span>Registrar takedown status transition update</span>
                  </label>
                </div>
              </div>

              <div className="pt-3 border-t border-brand-border/60 flex justify-end">
                <Button type="submit" isLoading={isSaving}>
                  Save Settings
                </Button>
              </div>
            </form>
          </Card>

        </div>

        {/* Team Members RBAC (4-cols) */}
        <div className="lg:col-span-4 space-y-6">
          <Card
            header={
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-[#111312]" />
                <h3 className="text-sm font-bold text-brand-dark">Security Team Access</h3>
              </div>
            }
          >
            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-2xl bg-brand-surface-light border border-brand-border">
                <div>
                  <p className="font-bold text-brand-dark">Elena Rostova</p>
                  <p className="text-[10px] text-brand-muted">elena@apexbank.com</p>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-[#111312] text-[#FBF5A5] text-[10px] font-bold border border-[#2B2D2C]">
                  Admin
                </span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-2xl bg-brand-surface-light border border-brand-border">
                <div>
                  <p className="font-bold text-brand-dark">Marcus Vance</p>
                  <p className="text-[10px] text-brand-muted">marcus.v@apexbank.com</p>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-[10px] font-bold border border-blue-200">
                  Analyst
                </span>
              </div>
            </div>
          </Card>
        </div>

      </div>

    </div>
  );
};
