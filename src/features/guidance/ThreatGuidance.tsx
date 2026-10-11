import React from 'react';
import { ShieldCheck, AlertCircle, PhoneCall, Key, Lock, ArrowRight, CheckCircle2 } from 'lucide-react';

interface ThreatReportGuidanceProps {
  reportId?: string;
  threatType?: string;
  onDone?: () => void;
}

export const ThreatReportGuidance: React.FC<ThreatReportGuidanceProps> = ({
  reportId,
  threatType = 'Phishing Impersonation',
  onDone,
}) => {
  return (
    <div className="bg-white rounded-2xl border border-stone-200 shadow-xl overflow-hidden p-6 md:p-8 space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600">
          <CheckCircle2 className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-stone-900">Threat Report Successfully Captured!</h2>
          <p className="text-xs text-stone-500">
            Reference Tracking ID: <span className="font-mono font-semibold text-stone-800">{reportId || 'BRD-78921-SCAM'}</span>
          </p>
        </div>
      </div>

      {/* What happens next */}
      <div className="bg-stone-50 rounded-xl p-5 border border-stone-200 space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-stone-600">
          What Happens Next in Our Pipeline
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
          <div className="p-3 bg-white rounded-lg border border-stone-200 shadow-2xs">
            <span className="font-bold text-emerald-600 block mb-1">1. AI Analysis</span>
            Analyzes homoglyphs, DNS, SSL, and visual trademarks in &lt; 5 seconds.
          </div>
          <div className="p-3 bg-white rounded-lg border border-stone-200 shadow-2xs">
            <span className="font-bold text-emerald-600 block mb-1">2. Brand Notified</span>
            Official brand security team receives high-priority triage incident.
          </div>
          <div className="p-3 bg-white rounded-lg border border-stone-200 shadow-2xs">
            <span className="font-bold text-emerald-600 block mb-1">3. Fast Takedown</span>
            Registrar abuse notice and DNS sinkhole request dispatched.
          </div>
          <div className="p-3 bg-white rounded-lg border border-stone-200 shadow-2xs">
            <span className="font-bold text-emerald-600 block mb-1">4. Live Updates</span>
            Check your dashboard anytime for real-time progress updates.
          </div>
        </div>
      </div>

      {/* Consumer victim safety steps */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-amber-700 flex items-center gap-1.5">
          <AlertCircle className="w-4 h-4" />
          Immediate Action Guide: If You Interacted with This Scam
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="p-4 bg-amber-50/60 rounded-xl border border-amber-200/80 text-xs space-y-1">
            <div className="flex items-center gap-2 font-bold text-amber-900">
              <Key className="w-4 h-4" />
              Shared Passwords?
            </div>
            <p className="text-stone-600">
              Immediately change your official account password and terminate existing active sessions.
            </p>
          </div>
          <div className="p-4 bg-amber-50/60 rounded-xl border border-amber-200/80 text-xs space-y-1">
            <div className="flex items-center gap-2 font-bold text-amber-900">
              <Lock className="w-4 h-4" />
              Enable Multi-Factor (2FA)
            </div>
            <p className="text-stone-600">
              Turn on authenticator app or hardware 2FA so stolen passwords cannot be used alone.
            </p>
          </div>
          <div className="p-4 bg-amber-50/60 rounded-xl border border-amber-200/80 text-xs space-y-1">
            <div className="flex items-center gap-2 font-bold text-amber-900">
              <PhoneCall className="w-4 h-4" />
              Entered Card / Bank Data?
            </div>
            <p className="text-stone-600">
              Call your financial institution's fraud hotline to temporarily freeze and reissue card numbers.
            </p>
          </div>
        </div>
      </div>

      {onDone && (
        <div className="pt-2 flex justify-end">
          <button
            onClick={onDone}
            className="px-5 py-2.5 bg-stone-900 hover:bg-stone-800 text-white text-xs font-bold rounded-xl transition-all flex items-center gap-2"
          >
            Return to Dashboard <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
