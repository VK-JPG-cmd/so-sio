import React, { useState } from 'react';
import { useBrand } from '../../context/BrandContext';
import { useNotification } from '../../context/NotificationContext';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { brandService } from '../../services/api';
import { 
  Building2, 
  Globe2, 
  Image, 
  Share2, 
  Smartphone, 
  ShieldCheck, 
  Plus, 
  CheckCircle2, 
  Copy, 
  Check, 
  ExternalLink,
  Key,
  Bell,
  Sparkles,
  Fingerprint,
  Save
} from 'lucide-react';

export const BrandProfileSettingsPage: React.FC = () => {
  const { currentBrand, refreshBrands } = useBrand();
  const { showToast } = useNotification();

  // Brand Profile Form State
  const [brandName, setBrandName] = useState(currentBrand?.name || 'ApexBank Global');
  const [legalEntity, setLegalEntity] = useState(currentBrand?.legalEntityName || 'Apex Financial Services Inc.');
  const [officialWebsite, setOfficialWebsite] = useState(currentBrand?.officialWebsite || 'https://apexbank.com');
  const [logoUrl, setLogoUrl] = useState(currentBrand?.logoUrl || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=120&auto=format&fit=crop&q=80');
  const [brandKeywords, setBrandKeywords] = useState('apex, apexbank, apex online, apex mobile, apex pay');
  const [industry, setIndustry] = useState(currentBrand?.industry || 'Banking & Fintech');

  // Verified Official Socials
  const [twitterHandle, setTwitterHandle] = useState('@ApexBankOfficial');
  const [instagramHandle, setInstagramHandle] = useState('@ApexBank');
  const [linkedinPage, setLinkedinPage] = useState('linkedin.com/company/apexbank');

  // Monitored Mobile Apps
  const [androidPackage, setAndroidPackage] = useState('com.apexbank.mobile');
  const [iosAppId, setIosAppId] = useState('id1498829102');

  const [isSaving, setIsSaving] = useState(false);
  const [isAddAssetModalOpen, setIsAddAssetModalOpen] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const [newAsset, setNewAsset] = useState({
    type: 'domain' as const,
    value: '',
  });

  const handleCopyRecord = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    showToast({ type: 'success', title: 'Copied', message: 'DNS TXT verification token copied.' });
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      showToast({
        type: 'success',
        title: 'Brand Profile Updated',
        message: 'Your brand perimeter and threat detection keywords have been updated.'
      });
    }, 600);
  };

  const handleAddAsset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAsset.value || !currentBrand) return;

    try {
      await brandService.addAsset(currentBrand.id, {
        type: newAsset.type,
        value: newAsset.value,
        status: 'pending',
        healthStatus: 'warning'
      });
      await refreshBrands();
      setIsAddAssetModalOpen(false);
      setNewAsset({ type: 'domain', value: '' });
      showToast({ type: 'success', title: 'Asset Added', message: 'New monitored perimeter asset created.' });
    } catch (err) {
      showToast({ type: 'error', title: 'Failed to add asset', message: 'Please try again.' });
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-brand-dark tracking-tight">Brand Profile & Settings</h1>
          <p className="text-xs text-brand-muted mt-1">
            Configure official brand identity, verified social accounts, keywords, and DNS defense parameters.
          </p>
        </div>

        <Button onClick={handleSaveProfile} isLoading={isSaving} leftIcon={<Save className="w-4 h-4" />}>
          Save Changes
        </Button>
      </div>

      <form onSubmit={handleSaveProfile} className="space-y-6">
        
        {/* SECTION 1: Core Brand Identity Details */}
        <Card
          header={
            <div className="flex items-center gap-2">
              <Building2 className="w-4 h-4 text-[#111312]" />
              <h3 className="text-sm font-bold text-brand-dark">Brand Identity & Official Web Perimeter</h3>
            </div>
          }
        >
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Brand Public Name"
                value={brandName}
                onChange={(e) => setBrandName(e.target.value)}
                placeholder="e.g. ApexBank Global"
                required
              />

              <Input
                label="Legal Registered Entity"
                value={legalEntity}
                onChange={(e) => setLegalEntity(e.target.value)}
                placeholder="e.g. Apex Financial Services Inc."
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Official Website URL"
                value={officialWebsite}
                onChange={(e) => setOfficialWebsite(e.target.value)}
                placeholder="https://apexbank.com"
                required
              />

              <div>
                <label className="block text-xs font-semibold text-brand-dark mb-1.5">Industry Sector</label>
                <select
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value as any)}
                  className="w-full rounded-2xl bg-white border border-brand-border px-4 py-2.5 text-xs font-bold text-brand-dark focus:outline-none focus:border-[#111312]"
                >
                  <option value="Banking & Fintech">Banking & Fintech</option>
                  <option value="E-commerce & Retail">E-commerce & Retail</option>
                  <option value="Healthcare">Healthcare</option>
                  <option value="SaaS & Enterprise">SaaS & Enterprise</option>
                  <option value="Crypto & Web3">Crypto & Web3</option>
                  <option value="Telecommunications">Telecommunications</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Brand Logo URL"
                value={logoUrl}
                onChange={(e) => setLogoUrl(e.target.value)}
                placeholder="https://.../logo.png"
                required
              />

              <Input
                label="Monitored Brand Keywords (Comma-separated for crawlers)"
                value={brandKeywords}
                onChange={(e) => setBrandKeywords(e.target.value)}
                placeholder="apex, apexbank, apex online, apex mobile"
                required
              />
            </div>
          </div>
        </Card>

        {/* SECTION 2: Verified Official Social Accounts */}
        <Card
          header={
            <div className="flex items-center gap-2">
              <Share2 className="w-4 h-4 text-[#111312]" />
              <h3 className="text-sm font-bold text-brand-dark">Verified Official Social Accounts</h3>
            </div>
          }
        >
          <div className="space-y-4">
            <p className="text-xs text-brand-muted">
              BrandShield AI references these authenticated handles to detect and report unauthorized impersonators.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                label="Official X (Twitter) Handle"
                value={twitterHandle}
                onChange={(e) => setTwitterHandle(e.target.value)}
                placeholder="@ApexBankOfficial"
              />

              <Input
                label="Official Instagram Handle"
                value={instagramHandle}
                onChange={(e) => setInstagramHandle(e.target.value)}
                placeholder="@ApexBank"
              />

              <Input
                label="Official LinkedIn URL"
                value={linkedinPage}
                onChange={(e) => setLinkedinPage(e.target.value)}
                placeholder="linkedin.com/company/apexbank"
              />
            </div>
          </div>
        </Card>

        {/* SECTION 3: Official Mobile App IDs */}
        <Card
          header={
            <div className="flex items-center gap-2">
              <Smartphone className="w-4 h-4 text-[#111312]" />
              <h3 className="text-sm font-bold text-brand-dark">Official Mobile Application Packages</h3>
            </div>
          }
        >
          <div className="space-y-4">
            <p className="text-xs text-brand-muted">
              Any mobile package on third-party stores mimicking these package identifiers will be flagged as rogue sideloaders.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Android Package Name (Google Play)"
                value={androidPackage}
                onChange={(e) => setAndroidPackage(e.target.value)}
                placeholder="com.apexbank.mobile"
              />

              <Input
                label="iOS Bundle / App Store ID (Apple)"
                value={iosAppId}
                onChange={(e) => setIosAppId(e.target.value)}
                placeholder="id1498829102"
              />
            </div>
          </div>
        </Card>

      </form>

      {/* SECTION 4: Monitored Assets & DNS Verification Records */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-brand-dark">Registered Assets & DNS Verification Tokens</h3>
            <p className="text-xs text-brand-muted">Monitored domains and cryptographic ownership verification records</p>
          </div>

          <Button
            size="sm"
            onClick={() => setIsAddAssetModalOpen(true)}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Add Monitored Asset
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {currentBrand?.assets.map((asset) => (
            <Card key={asset.id} className="space-y-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-2xl bg-[#111312] text-[#FBF5A5] border border-[#2B2D2C]">
                    <Globe2 className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="text-[10px] font-bold text-brand-muted uppercase tracking-wider">{asset.type.replace('_', ' ')}</span>
                    <h4 className="text-xs font-bold text-brand-dark truncate max-w-xs">{asset.value}</h4>
                  </div>
                </div>

                <Badge variant="status" status={asset.status} size="sm" />
              </div>

              {asset.dnsTxtRecord && (
                <div className="pt-2 border-t border-brand-border/60">
                  <div className="flex items-center justify-between text-[11px] text-brand-muted mb-1">
                    <span>DNS TXT Record:</span>
                    <button
                      type="button"
                      onClick={() => handleCopyRecord(asset.dnsTxtRecord!, asset.id)}
                      className="text-[#111312] hover:underline flex items-center gap-1 font-bold"
                    >
                      {copiedId === asset.id ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                      <span>Copy Record</span>
                    </button>
                  </div>
                  <p className="p-2 rounded-xl bg-brand-surface-light font-mono text-[11px] text-brand-dark truncate border border-brand-border/80">
                    {asset.dnsTxtRecord}
                  </p>
                </div>
              )}
            </Card>
          ))}
        </div>
      </div>

      {/* Add Monitored Asset Modal */}
      <Modal
        isOpen={isAddAssetModalOpen}
        onClose={() => setIsAddAssetModalOpen(false)}
        title="Add Monitored Asset"
        description="Include new domains, mobile package IDs, or social handles in your automated defense radar."
      >
        <form onSubmit={handleAddAsset} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-brand-dark mb-1.5">Asset Type</label>
            <select
              value={newAsset.type}
              onChange={(e) => setNewAsset({ ...newAsset, type: e.target.value as any })}
              className="w-full rounded-2xl bg-white border border-brand-border px-4 py-2.5 text-sm text-brand-dark focus:outline-none focus:border-[#111312] focus:ring-2 focus:ring-[#FBF5A5]"
            >
              <option value="domain">Official Domain</option>
              <option value="subdomain">Subdomain</option>
              <option value="social_handle">Social Handle (X, Instagram, LinkedIn)</option>
              <option value="mobile_app">Mobile App Package (Android/iOS)</option>
              <option value="trademark">Registered Trademark Wordmark</option>
            </select>
          </div>

          <Input
            label="Asset Value / Identifier"
            value={newAsset.value}
            onChange={(e) => setNewAsset({ ...newAsset, value: e.target.value })}
            placeholder="e.g. portal.apexbank.com or @ApexBankApp"
            required
          />

          <div className="flex justify-end gap-3 pt-3 border-t border-brand-border/60">
            <Button type="button" variant="outline" onClick={() => setIsAddAssetModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">
              Register Asset
            </Button>
          </div>
        </form>
      </Modal>

    </div>
  );
};
