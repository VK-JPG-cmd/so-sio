import React, { useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { AuthLayout } from '../../layouts/AuthLayout';
import { Button } from '../../components/ui/Button';
import { useBrand } from '../../context/BrandContext';
import { useNotification } from '../../context/NotificationContext';
import { brandService } from '../../services/api';
import { 
  Clock, 
  CheckCircle2, 
  RefreshCw, 
  Copy, 
  Check, 
  ExternalLink, 
  ArrowRight, 
  AlertTriangle,
  Code2,
  FileCheck2,
  Sparkles
} from 'lucide-react';
import confetti from 'canvas-confetti';

export const BrandVerificationPending: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { currentBrand, refreshBrands } = useBrand();
  const { showToast } = useNotification();

  const brand = location.state?.brand || currentBrand;
  const domainAsset = brand?.assets?.find((a: any) => a.type === 'domain') || brand?.assets?.[0];

  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationPassed, setVerificationPassed] = useState(brand?.verificationStatus === 'verified');
  const [activeTab, setActiveTab] = useState<'dns' | 'meta' | 'whois'>('dns');
  const [copied, setCopied] = useState(false);

  const dnsTxtRecord = domainAsset?.dnsTxtRecord || 'brandshield-verification=apex-bv7829-token';
  const metaTagContent = `<meta name="brandshield-site-verification" content="${dnsTxtRecord}" />`;

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    showToast({ type: 'success', title: 'Copied', message: 'Record copied to clipboard.' });
    setTimeout(() => setCopied(false), 2000);
  };

  const handleTestVerification = async () => {
    setIsVerifying(true);
    try {
      if (brand?.id && domainAsset?.id) {
        await brandService.verifyDnsTxtRecord(brand.id, domainAsset.id);
      } else {
        await new Promise((r) => setTimeout(r, 1200));
      }

      setVerificationPassed(true);
      await refreshBrands();
      confetti({ particleCount: 100, spread: 80, origin: { y: 0.6 } });
      showToast({ 
        type: 'success', 
        title: 'Domain Verified Successfully!', 
        message: `${brand?.name || 'Your brand'} is now officially verified on So-cio.` 
      });
    } catch (err: any) {
      showToast({ type: 'error', title: 'Verification Check Failed', message: 'DNS TXT record not detected yet. DNS propagation may take up to a few minutes.' });
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <AuthLayout
      mascotPose={verificationPassed ? 'celebrating' : 'scanning'}
      title={verificationPassed ? "Domain Ownership Verified!" : "Verification in Progress"}
      subtitle={
        verificationPassed
          ? "Congratulations! Your official brand perimeter has been established with authoritative takedown privileges."
          : "Complete domain verification to confirm authoritative ownership and unlock automated takedown pipelines."
      }
      badgeText={verificationPassed ? "Brand Status: Verified" : "Brand Status: Pending Verification"}
      backLink={{ to: '/brand-owner/overview', label: 'Go to Dashboard' }}
    >
      <div className="space-y-6">
        
        {/* Verification Status Card */}
        <div className={`p-6 rounded-3xl border transition-all ${
          verificationPassed
            ? 'bg-emerald-50/60 border-emerald-200 text-emerald-950'
            : 'bg-amber-50/60 border-amber-200 text-amber-950'
        }`}>
          <div className="flex items-start gap-3.5">
            <div className={`w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 ${
              verificationPassed ? 'bg-emerald-600 text-white' : 'bg-amber-500 text-white'
            }`}>
              {verificationPassed ? <CheckCircle2 className="w-6 h-6" /> : <Clock className="w-6 h-6 animate-pulse" />}
            </div>

            <div className="space-y-1 min-w-0">
              <h4 className="text-base font-bold">
                {verificationPassed ? 'Authoritative Verification Confirmed' : 'Awaiting DNS Record Confirmation'}
              </h4>
              <p className="text-xs opacity-85 leading-relaxed">
                {verificationPassed
                  ? `Domain ${domainAsset?.value || brand?.officialWebsite} is officially registered and verified.`
                  : `Please publish the verification token to your DNS records for ${domainAsset?.value || brand?.officialWebsite || 'your domain'}.`}
              </p>
            </div>
          </div>
        </div>

        {!verificationPassed ? (
          <div className="space-y-5">
            {/* Method Tabs */}
            <div className="flex bg-[#F8F7F4] p-1 rounded-2xl border border-brand-border">
              <button
                onClick={() => setActiveTab('dns')}
                className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all ${
                  activeTab === 'dns' ? 'bg-[#111312] text-white shadow-sm' : 'text-brand-muted hover:text-brand-dark'
                }`}
              >
                DNS TXT Record
              </button>
              <button
                onClick={() => setActiveTab('meta')}
                className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all ${
                  activeTab === 'meta' ? 'bg-[#111312] text-white shadow-sm' : 'text-brand-muted hover:text-brand-dark'
                }`}
              >
                HTML Meta Tag
              </button>
            </div>

            {/* Tab 1: DNS TXT */}
            {activeTab === 'dns' && (
              <div className="space-y-3">
                <p className="text-xs text-brand-muted">
                  Add the following TXT record in your DNS manager (e.g. Cloudflare, Route53, GoDaddy):
                </p>
                
                <div className="p-4 rounded-2xl bg-[#F8F7F4] border border-brand-border space-y-2 text-xs">
                  <div className="flex justify-between text-brand-muted">
                    <span>Host / Name: <strong className="text-brand-dark">@</strong> (or root)</span>
                    <span>Type: <strong className="text-brand-dark">TXT</strong></span>
                    <span>TTL: <strong className="text-brand-dark">300 (Auto)</strong></span>
                  </div>
                  <div className="flex items-center justify-between gap-2 p-2.5 rounded-xl bg-white border border-brand-border font-mono text-xs text-brand-dark">
                    <span className="truncate">{dnsTxtRecord}</span>
                    <button
                      onClick={() => handleCopy(dnsTxtRecord)}
                      className="p-1 rounded-lg text-[#111312] hover:bg-[#F4F3EF] shrink-0"
                    >
                      {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Tab 2: Meta Tag */}
            {activeTab === 'meta' && (
              <div className="space-y-3">
                <p className="text-xs text-brand-muted">
                  Paste this tag inside the <code className="text-[#111312] font-bold">&lt;head&gt;</code> element of your homepage:
                </p>
                
                <div className="flex items-center justify-between gap-2 p-3 rounded-2xl bg-white border border-brand-border font-mono text-xs text-brand-dark">
                  <span className="truncate">{metaTagContent}</span>
                  <button
                    onClick={() => handleCopy(metaTagContent)}
                    className="p-1 rounded-lg text-[#111312] hover:bg-[#F4F3EF] shrink-0"
                  >
                    {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="pt-2 space-y-3">
              <Button
                onClick={handleTestVerification}
                isLoading={isVerifying}
                className="w-full"
                size="lg"
                leftIcon={<RefreshCw className={`w-4 h-4 ${isVerifying ? 'animate-spin' : ''}`} />}
              >
                Scan & Verify DNS Record Now
              </Button>

              <p className="text-center text-[11px] text-brand-muted">
                Tip: Click above to simulate an immediate successful DNS resolution.
              </p>
            </div>
          </div>
        ) : (
          /* When Verified */
          <div className="space-y-4">
            <div className="p-4 rounded-2xl bg-white border border-brand-border shadow-sm space-y-2 text-xs">
              <div className="flex items-center justify-between py-1 border-b border-brand-border/50">
                <span className="text-brand-muted">Verified Entity:</span>
                <span className="font-bold text-brand-dark">{brand?.legalEntityName || 'Apex Financial Services Inc.'}</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-brand-border/50">
                <span className="text-brand-muted">Security Level:</span>
                <span className="font-bold text-emerald-700">Enterprise Verified (Tier 1)</span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="text-brand-muted">Active Protection:</span>
                <span className="font-bold text-[#111312]">Autonomous Takedown Desk Enabled</span>
              </div>
            </div>

            <Button
              onClick={() => navigate('/brand-owner/overview')}
              className="w-full"
              size="lg"
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Enter Brand Security Dashboard
            </Button>
          </div>
        )}

      </div>
    </AuthLayout>
  );
};
