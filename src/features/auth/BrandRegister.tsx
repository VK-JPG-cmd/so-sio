import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthLayout } from '../../layouts/AuthLayout';
import { Button } from '../../components/ui/Button';
import { Input, Textarea } from '../../components/ui/Input';
import { brandService } from '../../services/api';
import { useBrand } from '../../context/BrandContext';
import { useNotification } from '../../context/NotificationContext';
import { 
  Building2, 
  Globe2, 
  Image, 
  Share2, 
  ShieldCheck, 
  CheckCircle2, 
  ArrowRight, 
  ArrowLeft,
  Copy,
  Check,
  Upload,
  Lock,
  Sparkles
} from 'lucide-react';
import confetti from 'canvas-confetti';

export const BrandRegister: React.FC = () => {
  const [step, setStep] = useState<number>(1);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const { showToast } = useNotification();
  const { refreshBrands } = useBrand();
  const navigate = useNavigate();

  // Form State across 6 steps
  const [formData, setFormData] = useState({
    // Step 1: Business Info
    brandName: 'Nova Commerce',
    legalEntityName: 'Nova Digital Technologies Inc.',
    industry: 'E-commerce & Retail',
    description: 'Direct-to-consumer sustainable lifestyle platform with 50,000+ active customers.',
    // Step 2: Official Domain
    officialWebsite: 'https://novacommerce.io',
    subdomains: 'app.novacommerce.io, checkout.novacommerce.io',
    // Step 3: Logo & Brand Assets
    logoUrl: 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=120&auto=format&fit=crop&q=80',
    brandColors: '#111312, #FBF5A5',
    // Step 4: Official Social Links
    twitterHandle: '@NovaCommerceHQ',
    instagramHandle: '@novacommerce_official',
    linkedinUrl: 'https://linkedin.com/company/nova-commerce',
    // Step 5: Verification Method
    verificationMethod: 'dns_txt' as 'dns_txt' | 'meta_tag' | 'whois_email',
    dnsToken: 'brandshield-verification=nova-sec-token-2026-xyz',
    // Step 6: Confirmation
  });

  const [copiedToken, setCopiedToken] = useState(false);

  const handleCopyToken = () => {
    navigator.clipboard.writeText(formData.dnsToken);
    setCopiedToken(true);
    showToast({ type: 'success', title: 'Copied to Clipboard', message: 'DNS TXT verification string copied.' });
    setTimeout(() => setCopiedToken(false), 2000);
  };

  const handleNext = () => {
    if (step < 6) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const handleFinalSubmit = async () => {
    setIsLoading(true);
    try {
      const newBrand = await brandService.registerBrand({
        name: formData.brandName,
        legalEntityName: formData.legalEntityName,
        industry: formData.industry as any,
        officialWebsite: formData.officialWebsite,
        logoUrl: formData.logoUrl,
        description: formData.description,
      });

      await refreshBrands();
      confetti({ particleCount: 90, spread: 70, origin: { y: 0.6 } });
      showToast({ type: 'success', title: 'Brand Registered!', message: 'Verification record generated. Awaiting DNS validation.' });
      navigate('/auth/brand-verification-pending', { state: { brand: newBrand } });
    } catch (err: any) {
      showToast({ type: 'error', title: 'Registration Failed', message: err.message || 'Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const steps = [
    { num: 1, label: 'Business', icon: Building2 },
    { num: 2, label: 'Domain', icon: Globe2 },
    { num: 3, label: 'Assets', icon: Image },
    { num: 4, label: 'Socials', icon: Share2 },
    { num: 5, label: 'Verification', icon: Lock },
    { num: 6, label: 'Confirm', icon: CheckCircle2 },
  ];

  return (
    <AuthLayout
      mascotPose={step === 6 ? 'celebrating' : step === 5 ? 'scanning' : 'guarding'}
      title="Register Official Brand"
      subtitle="Establish your digital risk perimeter and get verified protection status across our network."
      badgeText={`Step ${step} of 6: ${steps[step - 1].label}`}
      backLink={{ to: '/auth/brand-login', label: 'Back to Sign In' }}
    >
      <div className="space-y-6">
        
        {/* Progress Bar & Step Badges */}
        <div>
          <div className="flex items-center justify-between gap-1 mb-3">
            {steps.map((s) => {
              const Icon = s.icon;
              const isPassed = step > s.num;
              const isCurrent = step === s.num;

              return (
                <div key={s.num} className="flex flex-col items-center flex-1">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                      isPassed
                        ? 'bg-[#2F7C5B] text-white'
                        : isCurrent
                        ? 'bg-[#111312] text-[#FBF5A5] shadow-sm ring-2 ring-[#111312]/30'
                        : 'bg-[#EFEFEA] text-[#737478] border border-[#DCDAD4]'
                    }`}
                  >
                    {isPassed ? <Check className="w-4 h-4" /> : <Icon className="w-3.5 h-3.5" />}
                  </div>
                  <span className={`text-[10px] mt-1 font-semibold hidden sm:block ${
                    isCurrent ? 'text-[#111312] font-bold' : 'text-[#737478]'
                  }`}>
                    {s.label}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="w-full h-1.5 bg-[#EFEFEA] rounded-full overflow-hidden">
            <div
              className="h-full bg-[#111312] transition-all duration-300"
              style={{ width: `${(step / 6) * 100}%` }}
            />
          </div>
        </div>

        {/* Step 1: Business Information */}
        {step === 1 && (
          <div className="space-y-4 animate-in fade-in duration-200">
            <div>
              <h3 className="text-lg font-bold text-brand-dark">Business Information</h3>
              <p className="text-xs text-brand-muted">Provide your legal business identity for verification.</p>
            </div>

            <Input
              label="Brand / Display Name"
              value={formData.brandName}
              onChange={(e) => setFormData({ ...formData, brandName: e.target.value })}
              placeholder="e.g. ApexBank or Nova Commerce"
              required
            />

            <Input
              label="Registered Legal Entity Name"
              value={formData.legalEntityName}
              onChange={(e) => setFormData({ ...formData, legalEntityName: e.target.value })}
              placeholder="e.g. Nova Digital Technologies Inc."
              helperText="Must match your corporate registration or trademark filings."
              required
            />

            <div>
              <label className="block text-xs font-semibold text-brand-dark mb-1.5">Industry Vertical</label>
              <select
                value={formData.industry}
                onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                className="w-full rounded-2xl bg-white border border-brand-border px-4 py-2.5 text-sm text-brand-dark focus:outline-none focus:border-[#111312] focus:ring-2 focus:ring-[#111312]/10"
              >
                <option>Banking & Fintech</option>
                <option>E-commerce & Retail</option>
                <option>SaaS & Enterprise</option>
                <option>Healthcare</option>
                <option>Crypto & Web3</option>
                <option>Telecommunications</option>
              </select>
            </div>

            <Textarea
              label="Brief Description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Tell consumers what your company offers..."
            />
          </div>
        )}

        {/* Step 2: Official Domain */}
        {step === 2 && (
          <div className="space-y-4 animate-in fade-in duration-200">
            <div>
              <h3 className="text-lg font-bold text-brand-dark">Official Domain & Hostnames</h3>
              <p className="text-xs text-brand-muted">The core root domain where customers securely interact with you.</p>
            </div>

            <Input
              label="Primary Official Domain URL"
              value={formData.officialWebsite}
              onChange={(e) => setFormData({ ...formData, officialWebsite: e.target.value })}
              placeholder="https://yourbrand.com"
              leftIcon={<Globe2 className="w-4 h-4" />}
              required
            />

            <Input
              label="Known Legitimate Subdomains (Comma-separated)"
              value={formData.subdomains}
              onChange={(e) => setFormData({ ...formData, subdomains: e.target.value })}
              placeholder="app.yourbrand.com, pay.yourbrand.com"
              helperText="Helps our crawler avoid flagging your genuine infrastructure."
            />

            <div className="p-3 rounded-2xl bg-blue-50 border border-blue-200 text-xs text-blue-800 space-y-1">
              <p className="font-bold">Domain Radar Ingestion:</p>
              <p className="text-[11px] leading-relaxed">
                So-cio will automatically monitor 450+ international TLD permutations (typos, lookalikes, IDN homoglyphs).
              </p>
            </div>
          </div>
        )}

        {/* Step 3: Logo & Brand Assets */}
        {step === 3 && (
          <div className="space-y-4 animate-in fade-in duration-200">
            <div>
              <h3 className="text-lg font-bold text-brand-dark">Logo & Visual Assets</h3>
              <p className="text-xs text-brand-muted">Used for perceptual hashing to catch cloned phishing pages.</p>
            </div>

            <div className="flex items-center gap-4 p-4 rounded-2xl bg-brand-surface-light border border-brand-border">
              <img
                src={formData.logoUrl}
                alt="Brand Logo Preview"
                className="w-16 h-16 rounded-2xl object-cover border border-brand-border shadow-sm shrink-0"
              />
              <div className="space-y-1">
                <p className="text-xs font-bold text-brand-dark">Vector Logo Asset</p>
                <p className="text-[11px] text-brand-muted">AI perceptual hash computed on upload.</p>
                <span className="inline-block text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-semibold border border-emerald-200">
                  Hash: 9f8a3c42 (Active)
                </span>
              </div>
            </div>

            <Input
              label="Logo Image URL"
              value={formData.logoUrl}
              onChange={(e) => setFormData({ ...formData, logoUrl: e.target.value })}
              placeholder="https://..."
              leftIcon={<Image className="w-4 h-4" />}
            />

            <Input
              label="Brand Primary Hex Colors"
              value={formData.brandColors}
              onChange={(e) => setFormData({ ...formData, brandColors: e.target.value })}
              placeholder="#111312, #FBF5A5"
            />
          </div>
        )}

        {/* Step 4: Official Social Links */}
        {step === 4 && (
          <div className="space-y-4 animate-in fade-in duration-200">
            <div>
              <h3 className="text-lg font-bold text-brand-dark">Official Social Channels</h3>
              <p className="text-xs text-brand-muted">Displayed on the Customer Portal so users know who is authentic.</p>
            </div>

            <Input
              label="Official X (Twitter) Handle"
              value={formData.twitterHandle}
              onChange={(e) => setFormData({ ...formData, twitterHandle: e.target.value })}
              placeholder="@YourBrandOfficial"
            />

            <Input
              label="Official Instagram Handle"
              value={formData.instagramHandle}
              onChange={(e) => setFormData({ ...formData, instagramHandle: e.target.value })}
              placeholder="@yourbrand"
            />

            <Input
              label="Official LinkedIn Page"
              value={formData.linkedinUrl}
              onChange={(e) => setFormData({ ...formData, linkedinUrl: e.target.value })}
              placeholder="https://linkedin.com/company/yourbrand"
            />
          </div>
        )}

        {/* Step 5: Ownership Verification */}
        {step === 5 && (
          <div className="space-y-4 animate-in fade-in duration-200">
            <div>
              <h3 className="text-lg font-bold text-brand-dark">Domain Ownership Verification</h3>
              <p className="text-xs text-brand-muted">Prove control of your primary domain to unlock authoritative takedowns.</p>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold text-brand-dark">Recommended: DNS TXT Record</label>
              <div className="p-3.5 rounded-2xl bg-[#F8F7F4] border border-brand-border space-y-2">
                <div className="flex items-center justify-between text-xs text-brand-muted">
                  <span>Host / Name: <code className="text-[#111312] font-bold">@</code></span>
                  <span>Type: <code className="text-[#111312] font-bold">TXT</code></span>
                </div>
                <div className="flex items-center justify-between gap-2 p-2 rounded-xl bg-white border border-brand-border font-mono text-xs text-brand-dark overflow-x-auto">
                  <span className="truncate">{formData.dnsToken}</span>
                  <button
                    type="button"
                    onClick={handleCopyToken}
                    className="p-1.5 rounded-lg text-[#111312] hover:bg-[#F4F3EF] shrink-0"
                    title="Copy DNS record value"
                  >
                    {copiedToken ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>

            <div className="p-3 rounded-2xl bg-[#F4F3EF] border border-[#E2E1DC] text-xs text-[#111312] space-y-1">
              <p className="font-bold flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[#111312]" />
                Live Verification Simulator Available
              </p>
              <p className="text-[11px] text-brand-muted leading-relaxed">
                After submission, our verification engine will query public DNS roots. You can trigger an instant verification scan in the next step.
              </p>
            </div>
          </div>
        )}

        {/* Step 6: Submission Confirmation */}
        {step === 6 && (
          <div className="space-y-4 animate-in fade-in duration-200">
            <div className="text-center py-2">
              <div className="w-14 h-14 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-3 border border-emerald-200 shadow-soft">
                <ShieldCheck className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-extrabold text-brand-dark">Ready to Initialize Protection</h3>
              <p className="text-xs text-brand-muted mt-1 max-w-sm mx-auto">
                Review your organization profile before establishing brand monitors.
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-brand-surface-light border border-brand-border space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-brand-border/50">
                <span className="text-brand-muted">Brand Name:</span>
                <span className="font-bold text-brand-dark">{formData.brandName}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-brand-border/50">
                <span className="text-brand-muted">Legal Entity:</span>
                <span className="font-bold text-brand-dark">{formData.legalEntityName}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-brand-border/50">
                <span className="text-brand-muted">Primary Domain:</span>
                <span className="font-bold text-[#111312]">{formData.officialWebsite}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-brand-muted">Verification Status:</span>
                <span className="font-bold text-amber-700">Pending DNS Confirmation</span>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between gap-3 pt-4 border-t border-brand-border/60">
          {step > 1 ? (
            <Button
              type="button"
              variant="outline"
              onClick={handleBack}
              leftIcon={<ArrowLeft className="w-4 h-4" />}
            >
              Back
            </Button>
          ) : (
            <div />
          )}

          {step < 6 ? (
            <Button
              type="button"
              onClick={handleNext}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Continue
            </Button>
          ) : (
            <Button
              type="button"
              onClick={handleFinalSubmit}
              isLoading={isLoading}
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
              rightIcon={<ShieldCheck className="w-4 h-4" />}
            >
              Submit & Launch Verification
            </Button>
          )}
        </div>

      </div>
    </AuthLayout>
  );
};
