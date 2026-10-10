import React, { useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { useBrand } from '../../context/BrandContext';
import { useAuth } from '../../context/AuthContext';
import { reportService } from '../../services/api';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input, Textarea } from '../../components/ui/Input';
import { useNotification } from '../../context/NotificationContext';
import { ReportCategory } from '../../types';
import { 
  AlertTriangle, 
  Globe2, 
  Share2, 
  MessageSquare, 
  Smartphone, 
  Mail, 
  Upload, 
  ShieldCheck, 
  CheckCircle2, 
  FileText, 
  Lock, 
  Sparkles,
  ArrowRight,
  HelpCircle,
  X
} from 'lucide-react';
import confetti from 'canvas-confetti';

export const SubmitReportPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { brands } = useBrand();
  const { user } = useAuth();
  const { showToast } = useNotification();

  const prefillUrl = location.state?.url || '';
  const prefillBrandId = location.state?.brandId || 'brand_apex_bank';

  const [category, setCategory] = useState<ReportCategory>('phishing_website');
  const [targetUrl, setTargetUrl] = useState<string>(prefillUrl);
  const [selectedBrandId, setSelectedBrandId] = useState<string>(prefillBrandId);
  const [description, setDescription] = useState<string>('');
  const [scamTactics, setScamTactics] = useState<string[]>([
    'Fake login screen',
    'Urgent account freeze warning'
  ]);
  const [evidenceFiles, setEvidenceFiles] = useState<Array<{ id: string; filename: string; url: string; fileType: string; uploadedAt: string }>>([]);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submittedReportId, setSubmittedReportId] = useState<string | null>(null);

  const categories = [
    { type: 'phishing_website' as const, label: 'Phishing Website', icon: Globe2, desc: 'Spoofed login or cloned website' },
    { type: 'fake_social_profile' as const, label: 'Fake Social Account', icon: Share2, desc: 'Impersonating brand care or exec' },
    { type: 'scam_sms_whatsapp' as const, label: 'Scam SMS / WhatsApp', icon: MessageSquare, desc: 'Smishing text or fake prize message' },
    { type: 'rogue_mobile_app' as const, label: 'Rogue Mobile App', icon: Smartphone, desc: 'Malicious APK or trojan clone' },
    { type: 'impersonation_email' as const, label: 'Impersonation Email', icon: Mail, desc: 'Spoofed sender or business email scam' },
  ];

  const availableTactics = [
    'Urgent account freeze warning',
    'Fake login screen',
    '2FA OTP code request in DM',
    'Fake cashback / prize offer',
    'Malicious APK download prompt',
    'Requesting cryptocurrency transfer'
  ];

  const toggleTactic = (tactic: string) => {
    if (scamTactics.includes(tactic)) {
      setScamTactics(scamTactics.filter(t => t !== tactic));
    } else {
      setScamTactics([...scamTactics, tactic]);
    }
  };

  const handleSimulateFileUpload = () => {
    const mockFile = {
      id: `file_${Date.now()}`,
      filename: `screenshot_scam_evidence_${evidenceFiles.length + 1}.png`,
      url: 'https://images.unsplash.com/photo-1563986768609-322da13575f3?w=400&auto=format&fit=crop&q=80',
      fileType: 'image/png',
      uploadedAt: new Date().toISOString()
    };
    setEvidenceFiles([...evidenceFiles, mockFile]);
    showToast({ type: 'info', title: 'Evidence Attached', message: `${mockFile.filename} added to investigation locker.` });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetUrl.trim()) {
      showToast({ type: 'error', title: 'Target Link Missing', message: 'Please provide the suspicious link or identifier.' });
      return;
    }

    setIsSubmitting(true);
    try {
      const selectedBrand = brands.find(b => b.id === selectedBrandId);
      const newReport = await reportService.submitReport({
        reporterUserId: user?.id || 'user_cust_1',
        reporterPhone: user?.phone || '+1 (555) 902-1144',
        brandId: selectedBrandId,
        brandName: selectedBrand?.name || 'Target Brand',
        category,
        targetUrlOrIdentifier: targetUrl,
        description: description || 'Customer flagged deceptive communication.',
        scamTactics,
        evidenceFiles
      });

      setSubmittedReportId(newReport.id);
      confetti({ particleCount: 80, spread: 70, origin: { y: 0.6 } });
      showToast({ 
        type: 'success', 
        title: 'Threat Report Dispatched!', 
        message: 'Your report was queued for priority triage and automated takedown.' 
      });
    } catch (err: any) {
      showToast({ type: 'error', title: 'Submission Failed', message: err.message || 'Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-200">
      
      {/* Title */}
      <div>
        <h1 className="text-2xl font-extrabold text-brand-dark tracking-tight">Report a Suspicious Threat or Scam</h1>
        <p className="text-xs text-brand-muted mt-1">
          Submit malicious URLs, spoofed profiles, or scam SMS. Your report is verified by AI and dispatched directly to the brand's security operations team.
        </p>
      </div>

      {!submittedReportId ? (
        <form onSubmit={handleSubmit} className="space-y-6">
          
          {/* Step 1: Category Selector */}
          <Card header={<h3 className="text-sm font-bold text-brand-dark">1. Select Threat Category</h3>}>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {categories.map((cat) => {
                const Icon = cat.icon;
                const isSelected = category === cat.type;

                return (
                  <button
                    key={cat.type}
                    type="button"
                    onClick={() => setCategory(cat.type)}
                    className={`p-4 rounded-2xl border text-left transition-all flex items-start gap-3 ${
                      isSelected
                        ? 'bg-[#111312] text-white border-[#111312] shadow-sm'
                        : 'bg-white hover:bg-[#F8F7F4] border-[#E2E1DC]'
                    }`}
                  >
                    <div className={`p-2.5 rounded-xl shrink-0 ${
                      isSelected ? 'bg-[#FBF5A5] text-[#111312]' : 'bg-[#F4F3EF] text-[#111312]'
                    }`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className={`text-xs font-bold ${isSelected ? 'text-white' : 'text-brand-dark'}`}>{cat.label}</h4>
                      <p className={`text-[11px] mt-0.5 ${isSelected ? 'text-white/80' : 'text-brand-muted'}`}>{cat.desc}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          </Card>

          {/* Step 2: Target Link & Brand Assignment */}
          <Card header={<h3 className="text-sm font-bold text-brand-dark">2. Suspicious Link & Target Brand</h3>}>
            <div className="space-y-4">
              <Input
                label="Suspicious URL, Social Handle, or Phone Number"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                placeholder="e.g. https://apex-bank-secure-login.net/verify or @ApexSupportBot"
                leftIcon={<AlertTriangle className="w-4 h-4 text-rose-500" />}
                required
              />

              <div>
                <label className="block text-xs font-semibold text-brand-dark mb-1.5">
                  Which brand is being impersonated?
                </label>
                <select
                  value={selectedBrandId}
                  onChange={(e) => setSelectedBrandId(e.target.value)}
                  className="w-full rounded-2xl bg-white border border-brand-border px-4 py-2.5 text-xs font-bold text-brand-dark focus:outline-none focus:border-[#111312]"
                >
                  {brands.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name} ({b.officialWebsite})
                    </option>
                  ))}
                  <option value="">Other / Unsure</option>
                </select>
              </div>
            </div>
          </Card>

          {/* Step 3: Scam Tactics Checklist */}
          <Card header={<h3 className="text-sm font-bold text-brand-dark">3. Observed Scam Tactics</h3>}>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {availableTactics.map((tactic) => {
                const checked = scamTactics.includes(tactic);
                return (
                  <button
                    key={tactic}
                    type="button"
                    onClick={() => toggleTactic(tactic)}
                    className={`p-3 rounded-2xl border text-left text-xs font-medium transition-all flex items-center justify-between ${
                      checked
                        ? 'bg-[#111312] border-[#111312] text-white font-bold'
                        : 'bg-white hover:bg-[#F8F7F4] border-[#E2E1DC] text-brand-dark'
                    }`}
                  >
                    <span>{tactic}</span>
                    <div className={`w-4 h-4 rounded-md flex items-center justify-center border ${
                      checked ? 'bg-[#FBF5A5] border-[#FBF5A5] text-[#111312]' : 'border-[#E2E1DC] bg-white'
                    }`}>
                      {checked && <CheckCircle2 className="w-3.5 h-3.5" />}
                    </div>
                  </button>
                );
              })}
            </div>
          </Card>

          {/* Step 4: Description & Evidence Upload */}
          <Card header={<h3 className="text-sm font-bold text-brand-dark">4. Description & Supporting Evidence</h3>}>
            <div className="space-y-4">
              <Textarea
                label="What happened? (Optional details)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Explain how you received this link, what the scammer asked for, etc..."
              />

              <div>
                <label className="block text-xs font-semibold text-brand-dark mb-1.5">Screenshots & Evidence</label>
                
                {/* Upload Button Box */}
                <div
                  onClick={handleSimulateFileUpload}
                  className="p-6 rounded-3xl border-2 border-dashed border-[#DCDAD4] hover:border-[#111312] bg-[#F8F7F4] hover:bg-[#F4F3EF] text-center cursor-pointer transition-all space-y-2"
                >
                  <div className="w-10 h-10 rounded-2xl bg-[#111312] text-[#FBF5A5] flex items-center justify-center mx-auto">
                    <Upload className="w-5 h-5" />
                  </div>
                  <p className="text-xs font-bold text-brand-dark">Click to attach screenshot or SMS evidence</p>
                  <p className="text-[11px] text-brand-muted">PNG, JPG, PDF up to 10MB</p>
                </div>

                {/* Attached Files Preview */}
                {evidenceFiles.length > 0 && (
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-3">
                    {evidenceFiles.map((file) => (
                      <div key={file.id} className="relative p-2 rounded-2xl bg-white border border-brand-border shadow-sm flex items-center gap-2">
                        <img src={file.url} alt="Evidence" className="w-10 h-10 rounded-xl object-cover" />
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-bold text-brand-dark truncate">{file.filename}</p>
                          <span className="text-[10px] text-emerald-700 font-semibold">Attached</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => setEvidenceFiles(evidenceFiles.filter(f => f.id !== file.id))}
                          className="p-1 text-brand-muted hover:text-rose-600"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </Card>

          {/* Privacy Notice & Submit Button */}
          <div className="p-4 rounded-2xl bg-[#F8F7F4] border border-brand-border text-xs text-brand-muted space-y-2">
            <div className="flex items-center gap-2 text-[#111312] font-bold">
              <Lock className="w-4 h-4" />
              <span>Consumer Privacy & Encryption Guarantee</span>
            </div>
            <p className="text-[11px] leading-relaxed">
              Your submission will be securely shared only with authorized security analysts and registrar abuse teams. We never sell reporter contact details.
            </p>
          </div>

          <Button
            type="submit"
            size="lg"
            className="w-full bg-rose-600 hover:bg-rose-700 text-white shadow-soft"
            isLoading={isSubmitting}
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            Submit Threat Report for Fast-Track Takedown
          </Button>

        </form>
      ) : (
        /* Submission Success Confirmation Screen */
        <Card className="text-center p-8 sm:p-12 space-y-6 animate-in fade-in duration-300">
          <div className="w-16 h-16 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto border border-emerald-200 shadow-soft">
            <CheckCircle2 className="w-9 h-9" />
          </div>

          <div className="space-y-2">
            <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider">Report Submitted Successfully</span>
            <h2 className="text-2xl font-extrabold text-brand-dark">Thank You For Keeping The Web Safe</h2>
            <p className="text-xs text-brand-muted max-w-md mx-auto leading-relaxed">
              Your report has been logged with Tracking ID <strong className="font-mono text-brand-dark">{submittedReportId}</strong>. Our automated pipeline is reviewing candidate threat telemetry.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-[#F8F7F4] border border-brand-border max-w-md mx-auto text-xs space-y-2 text-left">
            <div className="flex justify-between">
              <span className="text-brand-muted">Target:</span>
              <span className="font-mono font-bold text-brand-dark truncate max-w-[200px]">{targetUrl}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-brand-muted">Triage Status:</span>
              <span className="font-bold text-[#111312]">In Automated Triage</span>
            </div>
            <div className="flex justify-between">
              <span className="text-brand-muted">Updates:</span>
              <span className="text-brand-dark">SMS & Profile Timeline</span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-4">
            <Link to="/customer/my-reports">
              <Button size="lg">
                View in "My Reports" Tracker
              </Button>
            </Link>

            <Button
              variant="outline"
              size="lg"
              onClick={() => {
                setSubmittedReportId(null);
                setTargetUrl('');
                setDescription('');
                setEvidenceFiles([]);
              }}
            >
              Submit Another Report
            </Button>
          </div>
        </Card>
      )}

    </div>
  );
};
