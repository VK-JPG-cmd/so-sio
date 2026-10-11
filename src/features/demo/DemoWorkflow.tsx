import React, { useState } from 'react';
import { 
  Play, 
  CheckCircle2, 
  AlertTriangle, 
  ShieldAlert, 
  Globe, 
  Smartphone, 
  Share2, 
  ArrowRight, 
  Lock, 
  Search,
  Sparkles,
  ExternalLink
} from 'lucide-react';

interface DemoStep {
  id: number;
  title: string;
  category: 'onboarding' | 'domain' | 'social' | 'appstore' | 'scoring' | 'takedown';
  description: string;
  inputMock: Record<string, string>;
  outputResult: {
    title: string;
    score: number;
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    details: string[];
    action: string;
  };
}

const DEMO_STEPS: DemoStep[] = [
  {
    id: 1,
    title: 'Brand Onboarding & Asset Enrollment',
    category: 'onboarding',
    description: 'Enrolling brand trademarks, official domains, and mobile application package identifiers.',
    inputMock: {
      brandName: 'ApexBank Global',
      officialDomain: 'apexbank.com',
      playPackage: 'com.apexbank.mobile',
      twitterHandle: '@apexbank'
    },
    outputResult: {
      title: 'Multi-Factor Brand Authenticity Verified',
      score: 95,
      severity: 'LOW',
      details: [
        'DNS TXT Challenge: Verified (_brandshield-challenge.apexbank.com)',
        'SSL Certificate: Valid SHA-256 issued by DigiCert Inc.',
        'Official Brand Logo: Indexed pHash (a1b2c3d4e5f60718)',
        'Asset Whitelist: Registered 1 domain, 1 Twitter handle, 1 Play package'
      ],
      action: 'Brand enrolled with cryptographic trust stamp.'
    }
  },
  {
    id: 2,
    title: 'Lookalike Phishing Domain Detection',
    category: 'domain',
    description: 'Scanning suspicious lookalike domains with homoglyph, typosquatting, and SSL spoof analysis.',
    inputMock: {
      candidateUrl: 'https://apexbaηk-security-verify.net/login',
      detectedEngine: 'DomainTyposquatEngine'
    },
    outputResult: {
      title: 'Credential Harvesting Phishing Portal',
      score: 94,
      severity: 'CRITICAL',
      details: [
        'Homoglyph Substitution: Greek "η" replacing Latin "n"',
        'Lookalike Similarity: 91.4% match to apexbank.com',
        'Hosting Infrastructure: Bulletproof ASN hosted in anonymous offshore VPS',
        'SSL Fingerprint: Free Let\'s Encrypt cert issued < 24 hours ago'
      ],
      action: 'Flagged as High-Confidence Phishing Impersonation.'
    }
  },
  {
    id: 3,
    title: 'Social Media Impersonator Detection',
    category: 'social',
    description: 'Detecting fake customer support accounts across X/Twitter & Instagram using 4-factor weighted scoring.',
    inputMock: {
      fakeHandle: '@apexbank_support_desk',
      platform: 'Twitter / X',
      bio: '24/7 Official Account Resolution. Send DM with OTP to unfreeze.'
    },
    outputResult: {
      title: 'Customer Support Scam Profile',
      score: 88,
      severity: 'HIGH',
      details: [
        'Levenshtein Match: 84.2% name similarity to official brand (Weight: 40%)',
        'Keyword Exploitation: "support", "desk", "unfreeze" identified in bio',
        'Account Age Anomaly: Created 8 days ago (Weight: 20%)',
        'Follower Anomaly: 14 followers mimicking verified institution (Weight: 10%)'
      ],
      action: 'Tagged for automated platform imposter takedown request.'
    }
  },
  {
    id: 4,
    title: 'Rogue App Store & Permission Analysis',
    category: 'appstore',
    description: 'Deep static analysis of untrusted Android APKs and rogue Google Play lookalike packages.',
    inputMock: {
      appName: 'ApexBank Quick Pay & Balance',
      packageName: 'com.apexbank.quickpay.apk',
      store: 'Google Play Store / Third-Party APK'
    },
    outputResult: {
      title: 'Malicious Trojanized Mobile Banking App',
      score: 92,
      severity: 'CRITICAL',
      details: [
        'Package Identifier Spoofing: Lookalike bundle "com.apexbank.quickpay"',
        'Dangerous Capabilities: BIND_ACCESSIBILITY_SERVICE (Screen Reader Hijack)',
        'SMS Theft Privileges: READ_SMS & RECEIVE_SMS to steal banking 2FA',
        'Overlay Hijack: SYSTEM_ALERT_WINDOW to project fake login dialog'
      ],
      action: 'Dispatched Google Play Protect & rogue APK takedown report.'
    }
  },
  {
    id: 5,
    title: 'Automated Forensic Takedown Dispatch',
    category: 'takedown',
    description: 'Compiling evidence packages, registrar abuse emails, and legal notice webhooks.',
    inputMock: {
      targetThreat: 'apexbaηk-security-verify.net',
      evidenceArtifacts: 'DOM Snapshot, SSL Cert Chain, WHOIS Record, Screenshot'
    },
    outputResult: {
      title: 'Automated Registrar Takedown Notice Generated',
      score: 100,
      severity: 'LOW',
      details: [
        'Abuse Contact Identified: abuse@namesilo.com',
        'Digital Forensic Proof: Cryptographic hash manifest compiled',
        'DNS Sinkhole Request: Coordinated with Cloudflare / Google Safe Browsing',
        'Status Lifecycle: Transitioned from INVESTIGATING -> ACTION_TAKEN'
      ],
      action: 'Takedown packet dispatched via webhook & authenticated email.'
    }
  }
];

export const DemoWorkflow: React.FC = () => {
  const [activeStep, setActiveStep] = useState<number>(0);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const step = DEMO_STEPS[activeStep];

  const handleNext = () => {
    setIsRunning(true);
    setTimeout(() => {
      setActiveStep((prev) => (prev < DEMO_STEPS.length - 1 ? prev + 1 : 0));
      setIsRunning(false);
    }, 400);
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-500/10 text-red-600 border-red-200';
      case 'HIGH':
        return 'bg-amber-500/10 text-amber-600 border-amber-200';
      case 'MEDIUM':
        return 'bg-blue-500/10 text-blue-600 border-blue-200';
      default:
        return 'bg-emerald-500/10 text-emerald-600 border-emerald-200';
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-stone-200 shadow-xl overflow-hidden p-6 md:p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-stone-200 pb-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold uppercase tracking-wider mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            Interactive Evaluation Walkthrough
          </div>
          <h2 className="text-2xl font-black text-stone-900 tracking-tight">
            BrandShield AI End-to-End Threat Pipeline
          </h2>
          <p className="text-sm text-stone-600 mt-1">
            Simulate the entire detection lifecycle: Onboarding &rarr; Lookalike Domains &rarr; Social Impersonation &rarr; Rogue Mobile Apps &rarr; Legal Takedowns.
          </p>
        </div>
        <button
          onClick={handleNext}
          disabled={isRunning}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-stone-900 hover:bg-stone-800 text-white font-semibold rounded-xl text-sm transition-all shadow-md active:scale-95 disabled:opacity-50"
        >
          {isRunning ? (
            'Processing Engine...'
          ) : (
            <>
              Next Milestone ({activeStep + 1}/{DEMO_STEPS.length})
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>

      {/* Stepper Tabs */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
        {DEMO_STEPS.map((s, idx) => (
          <button
            key={s.id}
            onClick={() => setActiveStep(idx)}
            className={`flex flex-col items-start p-3 rounded-xl border text-left transition-all ${
              activeStep === idx
                ? 'bg-stone-900 text-white border-stone-900 shadow-sm'
                : 'bg-stone-50 hover:bg-stone-100 text-stone-700 border-stone-200'
            }`}
          >
            <span className="text-[10px] font-bold opacity-70">STEP 0{idx + 1}</span>
            <span className="text-xs font-bold truncate w-full mt-0.5">{s.title.split(' ')[0]} {s.title.split(' ')[1]}</span>
          </button>
        ))}
      </div>

      {/* Active Stage Simulation Body */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Input Payload Mock */}
        <div className="lg:col-span-5 bg-stone-50 rounded-xl p-5 border border-stone-200 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-stone-500">
              Simulated Ingestion Data
            </h3>
            <span className="text-xs font-mono bg-stone-200 text-stone-700 px-2 py-0.5 rounded">
              {step.category.toUpperCase()}
            </span>
          </div>

          <div className="space-y-3 font-mono text-xs">
            {Object.entries(step.inputMock).map(([key, val]) => (
              <div key={key} className="bg-white p-3 rounded-lg border border-stone-200/80 shadow-xs">
                <span className="text-stone-400 block text-[11px] mb-0.5">{key}</span>
                <span className="text-stone-900 font-semibold break-all">{val}</span>
              </div>
            ))}
          </div>

          <div className="pt-2 text-xs text-stone-500 italic">
            {step.description}
          </div>
        </div>

        {/* Right: Real-time Analysis Output */}
        <div className="lg:col-span-7 bg-white rounded-xl p-6 border border-stone-200 shadow-sm flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <span className="text-xs font-bold text-stone-400 uppercase tracking-wider">
                  Detection Engine Verdict
                </span>
                <h4 className="text-lg font-black text-stone-900 mt-1">
                  {step.outputResult.title}
                </h4>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${getSeverityBadge(step.outputResult.severity)}`}>
                  {step.outputResult.severity}
                </span>
                <span className="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-stone-100 text-stone-800 border border-stone-200">
                  Risk: {step.outputResult.score}/100
                </span>
              </div>
            </div>

            {/* Signal Details */}
            <div className="space-y-2">
              <span className="text-xs font-semibold text-stone-700">Forensic Signals & Evidence:</span>
              <div className="space-y-1.5">
                {step.outputResult.details.map((detail, dIdx) => (
                  <div key={dIdx} className="flex items-start gap-2 text-xs text-stone-600 bg-stone-50 p-2.5 rounded-lg border border-stone-200/60">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                    <span>{detail}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Action Taken */}
          <div className="bg-emerald-50 border border-emerald-200/80 rounded-xl p-4 flex items-center justify-between gap-4">
            <div className="flex items-center gap-2.5 text-xs font-medium text-emerald-900">
              <ShieldAlert className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{step.outputResult.action}</span>
            </div>
            <button
              onClick={handleNext}
              className="text-xs font-bold text-emerald-700 hover:text-emerald-900 hover:underline shrink-0 flex items-center gap-1"
            >
              Continue <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
