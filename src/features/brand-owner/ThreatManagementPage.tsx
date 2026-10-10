import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useBrand } from '../../context/BrandContext';
import { threatService } from '../../services/api';
import { SuspiciousThreat, ThreatSeverity, ThreatStatus } from '../../types';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { useNotification } from '../../context/NotificationContext';
import { 
  Search, 
  Filter, 
  ShieldAlert, 
  Send, 
  ExternalLink, 
  ArrowRight, 
  Sparkles, 
  Lightbulb, 
  Eye, 
  CheckCircle2, 
  AlertTriangle,
  Globe2,
  Smartphone,
  Users2
} from 'lucide-react';
import confetti from 'canvas-confetti';

export const ThreatManagementPage: React.FC = () => {
  const { currentBrand } = useBrand();
  const { showToast } = useNotification();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [threats, setThreats] = useState<SuspiciousThreat[]>([]);
  const [filteredThreats, setFilteredThreats] = useState<SuspiciousThreat[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedPlatform, setSelectedPlatform] = useState<string>(searchParams.get('category') || 'all');

  useEffect(() => {
    const loadThreats = async () => {
      setIsLoading(true);
      try {
        if (currentBrand) {
          const data = await threatService.getThreats(currentBrand.id);
          setThreats(data);
          setFilteredThreats(data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    loadThreats();
  }, [currentBrand]);

  // Handle Filtering & Searching
  useEffect(() => {
    let result = [...threats];

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(t => 
        t.targetDomainOrUrl.toLowerCase().includes(q) ||
        t.category.toLowerCase().includes(q) ||
        t.riskExplanation.toLowerCase().includes(q)
      );
    }

    if (selectedSeverity !== 'all') {
      result = result.filter(t => t.severity === selectedSeverity);
    }

    if (selectedStatus !== 'all') {
      result = result.filter(t => t.status === selectedStatus);
    }

    if (selectedPlatform !== 'all') {
      result = result.filter(t => t.category.includes(selectedPlatform));
    }

    setFilteredThreats(result);
  }, [searchQuery, selectedSeverity, selectedStatus, selectedPlatform, threats]);

  const handleQuickTakedown = async (threatId: string, domain: string) => {
    try {
      await threatService.updateThreatStatus(threatId, 'takedown_requested', 'Fast-track takedown dispatched from Threat Management console.');
      setThreats(threats.map(t => t.id === threatId ? { ...t, status: 'takedown_requested' } : t));
      confetti({ particleCount: 50, spread: 45 });
      showToast({ 
        type: 'success', 
        title: 'Takedown Initiated', 
        message: `Abuse package dispatched for ${domain}.` 
      });
    } catch (err: any) {
      showToast({ type: 'error', title: 'Action Failed', message: err.message });
    }
  };

  const getPlatformIcon = (category: string) => {
    if (category.includes('social') || category.includes('impersonation')) return Users2;
    if (category.includes('mobile')) return Smartphone;
    return Globe2;
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-brand-dark tracking-tight">Threat Management</h1>
          <p className="text-xs text-brand-muted mt-1">
            Search, filter, investigate, and review all detected brand impersonations and malicious assets.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link to="/brand-owner/recommended-actions">
            <Button variant="outline" size="sm" leftIcon={<Lightbulb className="w-4 h-4" />}>
              Recommended Actions
            </Button>
          </Link>
          <Link to="/brand-owner/ai-threat-explanation">
            <Button size="sm" leftIcon={<Sparkles className="w-4 h-4" />}>
              AI Threat Explanations
            </Button>
          </Link>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <Card padding="sm" className="space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          
          {/* Search Input */}
          <div className="lg:col-span-2 relative">
            <Search className="w-4 h-4 text-brand-muted absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search threat name, domain, URL, or keywords..."
              className="w-full pl-10 pr-4 py-2 text-xs rounded-2xl bg-brand-surface-light border border-brand-border focus:bg-white focus:outline-none focus:border-[#111312] transition-all"
            />
          </div>

          {/* Severity Filter */}
          <div>
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="w-full px-3 py-2 text-xs font-semibold rounded-2xl bg-brand-surface-light border border-brand-border text-brand-dark focus:outline-none focus:border-[#111312]"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical Severity</option>
              <option value="high">High Severity</option>
              <option value="medium">Medium Severity</option>
              <option value="low">Low Severity</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full px-3 py-2 text-xs font-semibold rounded-2xl bg-brand-surface-light border border-brand-border text-brand-dark focus:outline-none focus:border-[#111312]"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active Threats</option>
              <option value="under_investigation">Under Investigation</option>
              <option value="takedown_requested">Takedown In Progress</option>
              <option value="resolved">Resolved / Blocked</option>
              <option value="false_positive">Allowlisted / False Positive</option>
            </select>
          </div>

          {/* Platform / Vector Filter */}
          <div>
            <select
              value={selectedPlatform}
              onChange={(e) => setSelectedPlatform(e.target.value)}
              className="w-full px-3 py-2 text-xs font-semibold rounded-2xl bg-brand-surface-light border border-brand-border text-brand-dark focus:outline-none focus:border-[#111312]"
            >
              <option value="all">All Platforms</option>
              <option value="phishing">Fake Websites (Phishing)</option>
              <option value="typosquat">Typosquats</option>
              <option value="social">Fake Social Profiles</option>
              <option value="mobile">Suspicious Apps (APKs)</option>
            </select>
          </div>

        </div>
      </Card>

      {/* Threats Table */}
      <Card padding="none">
        <div className="p-4 border-b border-brand-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-brand-dark">Detected Threat Inventory</h3>
            <p className="text-xs text-brand-muted">Showing {filteredThreats.length} matching threat records</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-surface-light text-brand-muted border-b border-brand-border font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-6 py-3.5">Threat Target / Name</th>
                <th className="px-6 py-3.5">Platform</th>
                <th className="px-6 py-3.5">Risk Score</th>
                <th className="px-6 py-3.5">Severity</th>
                <th className="px-6 py-3.5">Detected Date</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border/60">
              {filteredThreats.length > 0 ? (
                filteredThreats.map((threat) => {
                  const PlatformIcon = getPlatformIcon(threat.category);

                  return (
                    <tr key={threat.id} className="hover:bg-brand-surface-light/40 transition-colors">
                      
                      {/* Threat Target */}
                      <td className="px-6 py-4 max-w-xs truncate">
                        <div className="flex items-center gap-2.5">
                          <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${
                            threat.severity === 'critical' ? 'bg-rose-500 animate-pulse' :
                            threat.severity === 'high' ? 'bg-orange-500' :
                            threat.severity === 'medium' ? 'bg-amber-500' : 'bg-emerald-500'
                          }`} />
                          <div>
                            <span className="font-mono font-bold text-brand-dark block truncate">
                              {threat.targetDomainOrUrl}
                            </span>
                            <span className="text-[11px] text-brand-muted line-clamp-1">
                              {threat.riskExplanation}
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Platform */}
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#F4F3EF] text-[#111312] font-semibold text-[11px] border border-[#DCDAD4]">
                          <PlatformIcon className="w-3.5 h-3.5 text-[#434346]" />
                          <span className="capitalize">{threat.category.replace(/_/g, ' ')}</span>
                        </span>
                      </td>

                      {/* Risk Score */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <span className="font-extrabold text-brand-dark text-sm">{threat.riskScore}</span>
                          <div className="w-12 h-1.5 bg-brand-surface rounded-full overflow-hidden">
                            <div
                              className={`h-full ${
                                threat.riskScore >= 90 ? 'bg-rose-600' :
                                threat.riskScore >= 70 ? 'bg-orange-500' :
                                threat.riskScore >= 40 ? 'bg-amber-500' : 'bg-emerald-500'
                              }`}
                              style={{ width: `${threat.riskScore}%` }}
                            />
                          </div>
                        </div>
                      </td>

                      {/* Severity */}
                      <td className="px-6 py-4">
                        <Badge severity={threat.severity} />
                      </td>

                      {/* Detected Date */}
                      <td className="px-6 py-4 text-brand-muted text-[11px]">
                        {new Date(threat.firstSeenAt).toLocaleDateString()}
                      </td>

                      {/* Status */}
                      <td className="px-6 py-4">
                        <Badge status={threat.status} />
                      </td>

                      {/* Action Buttons */}
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <Link to={`/brand-owner/threats/${threat.id}`}>
                            <Button variant="secondary" size="sm" title="Investigate Threat Details">
                              Investigate
                            </Button>
                          </Link>

                          {threat.status !== 'takedown_requested' && threat.status !== 'resolved' && (
                            <Button 
                              variant="outline" 
                              size="sm" 
                              onClick={() => handleQuickTakedown(threat.id, threat.targetDomainOrUrl)}
                              title="Request Takedown"
                            >
                              Takedown
                            </Button>
                          )}
                        </div>
                      </td>

                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-brand-muted text-xs">
                    No threats found matching your search or filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

    </div>
  );
};
