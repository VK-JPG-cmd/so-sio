import React from 'react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { 
  Smartphone, 
  ShieldAlert, 
  AlertOctagon, 
  DownloadCloud, 
  Lock, 
  ExternalLink,
  CheckCircle2,
  FileCode2,
  ShieldCheck
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const MobileAppRisksPage: React.FC = () => {
  const mobileRisks = [
    {
      id: 'app_1',
      title: 'ApexBank Mobile Assistant (Rogue APK v2.1.0)',
      sourcePlatform: 'Third-party APK Repository (apk-download-vault.ru)',
      packageName: 'com.apexbank.mobile.assistant.fake',
      sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      riskScore: 99,
      severity: 'critical' as const,
      status: 'under_investigation',
      detectedAt: '3 days ago',
      findings: [
        'DEX bytecode contains overlay injection targeting official banking app package.',
        'Requested permissions: BIND_ACCESSIBILITY_SERVICE and RECEIVE_SMS to steal 2FA codes.',
        'Hardcoded C2 telemetry server: https://c2-command.darknode.net/api/sink'
      ]
    },
    {
      id: 'app_2',
      title: 'Apex Rewards & Cashout Tool',
      sourcePlatform: 'Unofficial App Gallery mirror',
      packageName: 'org.rewards.apex.loot',
      sha256: '7a9c8b2100df9419bcf129482109849201948201948201948201948201948201',
      riskScore: 82,
      severity: 'high' as const,
      status: 'takedown_requested',
      detectedAt: '5 days ago',
      findings: [
        'Adware wrapper requiring users to enter banking debit card details for "payout processing".'
      ]
    }
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-brand-dark tracking-tight">Mobile App Risks & Malware Watch</h1>
          <p className="text-xs text-brand-muted mt-1">
            Detect rogue APKs, banking trojans, clone apps, and unauthorized repackaging targeting your mobile users.
          </p>
        </div>

        <div className="flex items-center gap-2 p-2.5 rounded-2xl bg-[#111312] border border-[#2B2D2C] text-xs font-bold text-[#FBF5A5]">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Official App Store Signatures Synced</span>
        </div>
      </div>

      {/* Official Package Baseline */}
      <Card className="bg-white border border-[#E2E1DC] shadow-sm">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-200">
              <Smartphone className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[10px] font-bold text-emerald-700 uppercase">Protected Baseline Asset</span>
              <h3 className="text-sm font-bold text-brand-dark">ApexBank Mobile (Official Android & iOS)</h3>
              <p className="text-xs font-mono text-brand-muted">Package: com.apexbank.mobile &bull; Cert SHA-256: 4F:9A:88:12:...</p>
            </div>
          </div>

          <Badge variant="status" status="verified" />
        </div>
      </Card>

      {/* Detected Rogue Packages */}
      <div className="space-y-6">
        <h3 className="text-sm font-bold text-brand-dark">Detected Rogue APK Clones & Malware Variants</h3>

        <div className="space-y-4">
          {mobileRisks.map((risk) => (
            <Card key={risk.id} className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-brand-border/60">
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-2xl bg-rose-50 text-rose-700 border border-rose-200">
                    <AlertOctagon className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-extrabold text-brand-dark">{risk.title}</h4>
                      <Badge severity={risk.severity} size="sm" />
                    </div>
                    <p className="text-xs text-brand-muted mt-0.5">Found on: {risk.sourcePlatform}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <div className="px-3 py-1 rounded-xl bg-red-50 text-[#8A1C2E] border border-red-200 text-xs font-bold">
                    Risk Score: {risk.riskScore}/100
                  </div>
                  <Badge status={risk.status} size="sm" />
                </div>
              </div>

              {/* Technical Malware Analysis Breakdown */}
              <div className="space-y-2">
                <span className="text-[11px] font-bold text-brand-muted uppercase tracking-wider">Static Bytecode & Telemetry Findings:</span>
                <div className="space-y-1.5">
                  {risk.findings.map((f, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-xs text-brand-dark/90 bg-brand-surface-light/60 p-2.5 rounded-xl border border-brand-border/60">
                      <FileCode2 className="w-3.5 h-3.5 text-rose-600 shrink-0 mt-0.5" />
                      <span>{f}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-2 flex items-center justify-between text-xs">
                <span className="font-mono text-[10px] text-brand-muted truncate max-w-sm">
                  SHA-256: {risk.sha256}
                </span>

                <Link to="/brand-owner/threats/threat_apex_04">
                  <Button variant="secondary" size="sm" rightIcon={<ExternalLink className="w-3.5 h-3.5" />}>
                    View Malware Dossier
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      </div>

    </div>
  );
};
