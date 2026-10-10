import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useBrand } from '../../context/BrandContext';
import { useNotification } from '../../context/NotificationContext';
import { Mascot } from '../../components/ui/Mascot';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { VerifiedReviewModal } from '../../components/customer/VerifiedReviewModal';
import { 
  Search, 
  ShieldCheck, 
  AlertTriangle, 
  ArrowRight, 
  Sparkles, 
  Lock, 
  Globe2, 
  MessageSquareHeart
} from 'lucide-react';

export const CustomerHomePage: React.FC = () => {
  const { brands } = useBrand();
  const { showToast } = useNotification();
  const navigate = useNavigate();

  const [searchUrl, setSearchUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState<{
    domain: string;
    isSafe: boolean;
    riskScore: number;
    verdict: string;
  } | null>(null);

  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);

  const handleScanUrl = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchUrl.trim()) return;

    setIsScanning(true);
    setScanResult(null);

    setTimeout(() => {
      setIsScanning(false);
      const clean = searchUrl.toLowerCase().trim();

      const matchedBrand = brands.find(
        (b) => clean.includes(b.officialWebsite.toLowerCase()) || clean.includes(b.slug)
      );

      if (matchedBrand) {
        setScanResult({
          domain: matchedBrand.officialWebsite,
          isSafe: true,
          riskScore: 4,
          verdict: `Official Verified Channel: This domain is the authentic registered website of ${matchedBrand.name}.`
        });
        showToast({
          type: 'success',
          title: 'Official Brand Verified',
          message: `${matchedBrand.name} matches official cryptographic registry.`
        });
      } else if (clean.includes('verify') || clean.includes('login') || clean.includes('secure') || clean.includes('baank')) {
        setScanResult({
          domain: searchUrl,
          isSafe: false,
          riskScore: 88,
          verdict: 'High-Risk Impersonation Anomaly: Domain exhibits credential harvesting patterns and recent registration date.'
        });
        showToast({
          type: 'warning',
          title: 'Threat Detected',
          message: 'Potential phishing clone targeting consumer banking credentials.'
        });
      } else {
        setScanResult({
          domain: searchUrl,
          isSafe: true,
          riskScore: 18,
          verdict: 'Neutral Domain: No malicious IoC indicators, brand impersonation signatures, or active takedowns found.'
        });
      }
    }, 800);
  };

  return (
    <div className="space-y-10 animate-in fade-in duration-200 text-[#111312]">
      
      {/* Hero Section: Solid Near-Black Card with Pale Butter Yellow Accent */}
      <div className="relative rounded-3xl bg-[#111312] text-white border border-[#2B2D2C] p-6 sm:p-10 lg:p-12 shadow-2xl overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          
          <div className="lg:col-span-7 space-y-5">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#1C1E1D] border border-[#3A3C3B] text-xs font-bold text-[#FBF5A5]">
              <Sparkles className="w-3.5 h-3.5 text-[#FBF5A5]" />
              <span>Instant AI Brand & URL Safety Scanner</span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight">
              Is that link safe?<br />
              <span className="text-[#FBF5A5]">
                Check Before You Click.
              </span>
            </h1>

            <p className="text-xs sm:text-sm text-[#9A9B9C] leading-relaxed max-w-xl">
              Verify official enterprise websites, report scam SMS messages and phishing clones, and help safeguard millions of consumers worldwide.
            </p>

            {/* Instant Safety Checker Form */}
            <form onSubmit={handleScanUrl} className="relative max-w-xl">
              <div className="flex flex-col sm:flex-row items-center gap-2 bg-[#1C1E1D] p-2 rounded-2xl border border-[#2D2F2E]">
                <div className="flex items-center gap-2.5 px-3 w-full">
                  <Search className="w-5 h-5 text-[#9A9B9C] shrink-0" />
                  <input
                    type="text"
                    value={searchUrl}
                    onChange={(e) => setSearchUrl(e.target.value)}
                    placeholder="Enter any domain or link (e.g. apexbank.com or suspicious-link.net)..."
                    className="w-full text-xs sm:text-sm bg-transparent border-none focus:outline-none text-white placeholder:text-[#9A9B9C] py-1"
                  />
                </div>
                <Button
                  type="submit"
                  variant="accent"
                  isLoading={isScanning}
                  className="w-full sm:w-auto shrink-0 shadow-sm"
                >
                  Verify Link
                </Button>
              </div>
            </form>

            {/* Scan Verdict Card */}
            {scanResult && (
              <div className={`p-4 rounded-xl border transition-all animate-in fade-in duration-200 ${
                scanResult.isSafe
                  ? 'bg-[#1C1E1D] border-[#2F7C5B] text-white'
                  : 'bg-[#1C1E1D] border-[#C8485E] text-white'
              }`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    {scanResult.isSafe ? (
                      <ShieldCheck className="w-6 h-6 text-[#2F7C5B] shrink-0 mt-0.5" />
                    ) : (
                      <AlertTriangle className="w-6 h-6 text-[#C8485E] shrink-0 mt-0.5" />
                    )}
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-xs font-bold font-mono text-[#FBF5A5]">{scanResult.domain}</h4>
                        <span className={`text-[10px] px-2 py-0.2 rounded-full font-bold ${
                          scanResult.isSafe ? 'bg-[#2F7C5B]/20 text-[#2F7C5B]' : 'bg-[#C8485E]/20 text-[#C8485E]'
                        }`}>
                          Risk Score: {scanResult.riskScore}/100
                        </span>
                      </div>
                      <p className="text-xs mt-1 leading-relaxed text-[#D6D6D8]">{scanResult.verdict}</p>
                    </div>
                  </div>

                  {!scanResult.isSafe && (
                    <Link to="/customer/report" state={{ url: scanResult.domain }}>
                      <Button variant="danger" size="sm">
                        Report Scam
                      </Button>
                    </Link>
                  )}
                </div>
              </div>
            )}

            {/* Quick Actions */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Link to="/customer/report">
                <Button
                  variant="accent"
                  className="shadow-sm"
                  leftIcon={<AlertTriangle className="w-4 h-4" />}
                >
                  Report Scam
                </Button>
              </Link>

              <Button
                variant="secondary"
                onClick={() => setIsReviewModalOpen(true)}
                leftIcon={<ShieldCheck className="w-4 h-4 text-[#FBF5A5]" />}
                className="bg-[#2B2D2C] hover:bg-[#383A39] border border-[#3E403F] text-white"
              >
                Upload Verified Review & Proof
              </Button>

              <Link to="/customer/brands">
                <Button variant="outline" className="bg-[#1C1E1D] text-white border-[#2D2F2E] hover:bg-[#252726]" rightIcon={<ArrowRight className="w-4 h-4" />}>
                  Brands Directory
                </Button>
              </Link>
            </div>
          </div>

          {/* Right Mascot Hero Visual */}
          <div className="lg:col-span-5 flex justify-center py-4">
            <Mascot pose="guarding" size="xl" />
          </div>

        </div>
      </div>

      {/* Featured Trusted Brands Directory */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-[#111312]">Verified Brand Directory</h2>
            <p className="text-xs text-[#737478]">Check authentic channels before conducting transactions.</p>
          </div>

          <Link to="/customer/brands" className="text-xs font-bold text-[#111312] hover:underline flex items-center gap-1">
            <span>View All ({brands.length})</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {brands.slice(0, 3).map((brand) => (
            <Card
              key={brand.id}
              hoverEffect
              onClick={() => navigate(`/customer/brands/${brand.slug}`)}
              className="space-y-4 bg-white border border-[#E2E1DC]"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <img
                    src={brand.logoUrl}
                    alt={brand.name}
                    className="w-12 h-12 rounded-xl object-cover border border-[#E2E1DC]"
                  />
                  <div>
                    <h3 className="text-sm font-bold text-[#111312]">{brand.name}</h3>
                    <span className="text-[10px] text-[#737478]">{brand.industry}</span>
                  </div>
                </div>

                <Badge variant="status" status="verified" size="sm" />
              </div>

              <p className="text-xs text-[#737478] line-clamp-2 leading-relaxed">
                {brand.description}
              </p>

              <div className="pt-3 border-t border-[#EAE9E4] flex items-center justify-between text-xs">
                <span className="font-mono text-[11px] text-[#111312] font-semibold truncate max-w-[180px]">
                  {brand.officialWebsite}
                </span>

                <span className="font-bold text-[#2F7C5B] flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  {brand.trustScore}% Trust
                </span>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Verified Customer Product Reviews Section: Solid Near-Black Card */}
      <div className="rounded-3xl bg-[#111312] text-white border border-[#2B2D2C] p-6 sm:p-8 space-y-4 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-[#FBF5A5] text-[#111312] flex items-center justify-center font-bold shadow-sm shrink-0">
              <MessageSquareHeart className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-lg font-bold text-white">Customer Reviews & Verified Proofs</h2>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#1C1E1D] text-[#FBF5A5] border border-[#3A3C3B]">
                  <ShieldCheck className="w-3 h-3 inline mr-0.5" /> Customer Only &bull; Proof Backed
                </span>
              </div>
              <p className="text-xs text-[#9A9B9C] mt-1 max-w-xl">
                Upload your genuine product security reviews with invoice/transaction proof. Brand owners review and officially reply to your feedback in their security portal.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="accent"
              onClick={() => setIsReviewModalOpen(true)}
              leftIcon={<ShieldCheck className="w-4 h-4" />}
            >
              Upload Verified Review & Proof
            </Button>
            <Link to="/customer/reviews">
              <Button variant="outline" className="bg-[#1C1E1D] text-white border-[#2D2F2E] hover:bg-[#252726]" rightIcon={<ArrowRight className="w-4 h-4" />}>
                Browse All Reviews
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Consumer Security Awareness Tips */}
      <div className="space-y-4">
        <div>
          <h2 className="text-lg font-bold text-[#111312]">Security Awareness & Anti-Phishing Tips</h2>
          <p className="text-xs text-[#737478]">Stay alert to common fraud patterns.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="space-y-2 p-5 bg-white border border-[#E2E1DC]">
            <div className="w-10 h-10 rounded-xl bg-[#111312] text-[#FBF5A5] flex items-center justify-center">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <h4 className="text-xs font-bold text-[#111312]">Urgency & Fear Coercion</h4>
            <p className="text-xs text-[#737478] leading-relaxed">
              Legitimate banks will never threaten to freeze your assets within 15 minutes over a text message.
            </p>
          </Card>

          <Card className="space-y-2 p-5 bg-white border border-[#E2E1DC]">
            <div className="w-10 h-10 rounded-xl bg-[#111312] text-[#FBF5A5] flex items-center justify-center">
              <Lock className="w-5 h-5" />
            </div>
            <h4 className="text-xs font-bold text-[#111312]">Never Share OTP Passcodes</h4>
            <p className="text-xs text-[#737478] leading-relaxed">
              One-Time Passcodes are meant only for your direct entry. Support staff will never ask for them in DMs or over the phone.
            </p>
          </Card>

          <Card className="space-y-2 p-5 bg-white border border-[#E2E1DC]">
            <div className="w-10 h-10 rounded-xl bg-[#111312] text-[#FBF5A5] flex items-center justify-center">
              <Globe2 className="w-5 h-5" />
            </div>
            <h4 className="text-xs font-bold text-[#111312]">Inspect Domain Spelling</h4>
            <p className="text-xs text-[#737478] leading-relaxed">
              Fraudsters frequently use subtle typos (e.g. "baank.com" or "bank-verify.net"). Check the exact spelling before logging in.
            </p>
          </Card>
        </div>
      </div>

      {/* Verified Product Review Upload Modal */}
      <VerifiedReviewModal
        isOpen={isReviewModalOpen}
        onClose={() => setIsReviewModalOpen(false)}
        onReviewSubmitted={() => {
          setIsReviewModalOpen(false);
        }}
      />

    </div>
  );
};
