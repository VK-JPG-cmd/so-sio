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
  Fingerprint, 
  Globe2, 
  Image, 
  Share2, 
  Smartphone, 
  ShieldCheck, 
  Plus, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  Copy, 
  Check, 
  ExternalLink,
  Shield,
  Sparkles
} from 'lucide-react';

export const BrandIdentityPage: React.FC = () => {
  const { currentBrand, refreshBrands } = useBrand();
  const { showToast } = useNotification();
  const [isAddAssetModalOpen, setIsAddAssetModalOpen] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const [newAsset, setNewAsset] = useState({
    type: 'domain' as const,
    value: '',
  });

  const handleCopyRecord = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    showToast({ type: 'success', title: 'Copied', message: 'Verification record copied.' });
    setTimeout(() => setCopiedId(null), 2000);
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
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-brand-dark tracking-tight">Official Brand Identity & Perimeter</h1>
          <p className="text-xs text-brand-muted mt-1">
            Manage your authenticated domains, trademark hashes, social channels, and DNS verification records.
          </p>
        </div>

        <Button
          onClick={() => setIsAddAssetModalOpen(true)}
          leftIcon={<Plus className="w-4 h-4" />}
        >
          Add Monitored Asset
        </Button>
      </div>

      {/* Brand Entity Card */}
      <Card>
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            <img
              src={currentBrand?.logoUrl}
              alt={currentBrand?.name}
              className="w-20 h-20 rounded-3xl object-cover border border-brand-border shadow-soft"
            />
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-brand-dark">{currentBrand?.name}</h2>
                <Badge variant="status" status={currentBrand?.verificationStatus || 'verified'} />
              </div>
              <p className="text-xs text-brand-muted">Legal Entity: <span className="font-semibold text-brand-dark">{currentBrand?.legalEntityName}</span></p>
              <p className="text-xs text-[#111312] font-mono font-medium flex items-center gap-1.5">
                <Globe2 className="w-3.5 h-3.5" />
                <span>{currentBrand?.officialWebsite}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6 p-4 rounded-2xl bg-[#F8F7F4] border border-brand-border text-center">
            <div>
              <p className="text-[10px] uppercase font-bold text-brand-muted tracking-wider">Perimeter Trust</p>
              <p className="text-2xl font-extrabold text-emerald-600">{currentBrand?.trustScore || 98}%</p>
            </div>
            <div className="w-px h-10 bg-brand-border" />
            <div>
              <p className="text-[10px] uppercase font-bold text-brand-muted tracking-wider">Monitored Assets</p>
              <p className="text-2xl font-extrabold text-[#111312]">{currentBrand?.assets.length || 5}</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Assets Grid */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-brand-dark">Registered Assets & DNS Status</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {currentBrand?.assets.map((asset) => {
            const iconMap = {
              domain: Globe2,
              subdomain: Globe2,
              logo: Image,
              social_handle: Share2,
              mobile_app: Smartphone,
              trademark: Fingerprint
            }[asset.type];

            const Icon = iconMap || Globe2;

            return (
              <Card key={asset.id} className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-2xl bg-[#F4F3EF] text-[#111312] border border-[#E2E1DC]">
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-brand-muted uppercase tracking-wider">{asset.type.replace('_', ' ')}</span>
                      <h4 className="text-sm font-bold text-brand-dark truncate max-w-[200px] sm:max-w-xs">{asset.value}</h4>
                    </div>
                  </div>

                  <Badge variant="status" status={asset.status} size="sm" />
                </div>

                {asset.dnsTxtRecord && (
                  <div className="pt-2 border-t border-brand-border/60">
                    <div className="flex items-center justify-between text-[11px] text-brand-muted mb-1">
                      <span>DNS TXT Record:</span>
                      <button
                        onClick={() => handleCopyRecord(asset.dnsTxtRecord!, asset.id)}
                        className="text-[#111312] hover:underline flex items-center gap-1 font-bold"
                      >
                        {copiedId === asset.id ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                        <span>Copy Token</span>
                      </button>
                    </div>
                    <p className="p-2 rounded-xl bg-brand-surface-light font-mono text-[11px] text-brand-dark truncate border border-brand-border/80">
                      {asset.dnsTxtRecord}
                    </p>
                  </div>
                )}
              </Card>
            );
          })}
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
              className="w-full rounded-2xl bg-white border border-brand-border px-4 py-2.5 text-sm text-brand-dark focus:outline-none focus:border-[#111312] focus:ring-2 focus:ring-[#111312]/10"
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

          <div className="p-3 rounded-2xl bg-[#F8F7F4] border border-brand-border text-xs text-brand-muted space-y-1">
            <p className="font-bold text-[#111312]">Automated Perimeter Defense:</p>
            <p className="text-[11px] leading-relaxed">
              Once added, BrandShield AI will scan for lookalikes, unauthorized cloning, and rogue API calls targeting this asset.
            </p>
          </div>

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
