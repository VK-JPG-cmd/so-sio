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
  Users2,
  RotateCcw
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { 
  DateFilterDropdown, 
  DateFilterValue, 
  ThreatFilterDropdown, 
  ThreatFilterKey 
} from '../../components/ui/filters';

export const ThreatManagementPage: React.FC = () => {
  const { currentBrand } = useBrand();
  const { showToast } = useNotification();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [threats, setThreats] = useState<SuspiciousThreat[]>([]);
  const [filteredThreats, setFilteredThreats] = useState<SuspiciousThreat[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const [searchQuery, setSearchQuery] = useState('');
  const [threatFilter, setThreatFilter] = useState<ThreatFilterKey>(
    (searchParams.get('severity') as ThreatFilterKey) || 
    (searchParams.get('status') as ThreatFilterKey) || 
    'all'
  );
  const [dateFilter, setDateFilter] = useState<DateFilterValue>({
    preset: '30d',
    label: '30 days'
  });
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

  // Compute live threat counts by filter option for the dropdown badges
  const threatFilterCounts = React.useMemo(() => {
    const anchorTimestamp = new Date('2026-10-10T23:59:59Z').getTime();
    const inDateThreats = threats.filter((t) => {
      const threatTime = new Date(t.firstSeenAt).getTime();
      if (dateFilter.preset === 'custom' && dateFilter.startDate && dateFilter.endDate) {
        const start = new Date(`${dateFilter.startDate}T00:00:00Z`).getTime();
        const end = new Date(`${dateFilter.endDate}T23:59:59Z`).getTime();
        return threatTime >= start && threatTime <= end;
      }
      const days = 
        dateFilter.preset === '7d' ? 7 :
        dateFilter.preset === '14d' ? 14 :
        dateFilter.preset === '30d' ? 30 :
        dateFilter.preset === '60d' ? 60 :
        dateFilter.preset === '90d' ? 90 : 30;
      return threatTime >= (anchorTimestamp - days * 24 * 60 * 60 * 1000);
    });

    return {
      all: inDateThreats.length,
      critical: inDateThreats.filter(t => t.severity === 'critical').length,
      high: inDateThreats.filter(t => t.severity === 'high').length,
      medium: inDateThreats.filter(t => t.severity === 'medium').length,
      low: inDateThreats.filter(t => t.severity === 'low').length,
      active: inDateThreats.filter(t => t.status === 'active').length,
      under_investigation: inDateThreats.filter(t => t.status === 'under_investigation').length,
      takedown_requested: inDateThreats.filter(t => t.status === 'takedown_requested').length,
      resolved: inDateThreats.filter(t => t.status === 'resolved').length,
    };
  }, [threats, dateFilter]);

  // Handle Filtering & Searching
  useEffect(() => {
    let result = [...threats];
    const anchorTimestamp = new Date('2026-10-10T23:59:59Z').getTime();

    // 1. Search Query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(t => 
        t.targetDomainOrUrl.toLowerCase().includes(q) ||
        t.category.toLowerCase().includes(q) ||
        t.riskExplanation.toLowerCase().includes(q)
      );
    }

    // 2. Date Range Filter
    result = result.filter((t) => {
      const threatTime = new Date(t.firstSeenAt).getTime();
      if (dateFilter.preset === 'custom' && dateFilter.startDate && dateFilter.endDate) {
        const start = new Date(`${dateFilter.startDate}T00:00:00Z`).getTime();
        const end = new Date(`${dateFilter.endDate}T23:59:59Z`).getTime();
        return threatTime >= start && threatTime <= end;
      }
      const days = 
        dateFilter.preset === '7d' ? 7 :
        dateFilter.preset === '14d' ? 14 :
        dateFilter.preset === '30d' ? 30 :
        dateFilter.preset === '60d' ? 60 :
        dateFilter.preset === '90d' ? 90 : 30;
      const cutoff = anchorTimestamp - (days * 24 * 60 * 60 * 1000);
      return threatTime >= cutoff;
    });

    // 3. Unified Threat Filter (Severity or Status)
    if (threatFilter !== 'all') {
      if (['critical', 'high', 'medium', 'low'].includes(threatFilter)) {
        result = result.filter(t => t.severity === threatFilter);
      } else if (['active', 'under_investigation', 'takedown_requested', 'resolved'].includes(threatFilter)) {
        result = result.filter(t => t.status === threatFilter);
      }
    }

    // 4. Platform Filter
    if (selectedPlatform !== 'all') {
      result = result.filter(t => t.category.includes(selectedPlatform));
    }

    setFilteredThreats(result);
  }, [searchQuery, threatFilter, dateFilter, selectedPlatform, threats]);

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
              Why is this a threat?
            </Button>
          </Link>
        </div>
      </div>

      {/* Filter & Search Bar with Reference Dropdowns */}
      <Card padding="sm" className="space-y-3">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
          
          {/* Search Input */}
          <div className="flex-1 relative min-w-[240px]">
            <Search className="w-4 h-4 text-brand-muted absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search website, evidence, account name, ticket..."
              className="w-full pl-10 pr-4 py-2 text-xs rounded-2xl bg-brand-surface-light border border-brand-border focus:bg-white focus:outline-none focus:border-[#111312] transition-all"
            />
          </div>

          <div className="flex items-center gap-2.5 flex-wrap">
            {/* Threat Filter Dropdown */}
            <ThreatFilterDropdown
              value={threatFilter}
              onChange={setThreatFilter}
              counts={threatFilterCounts}
              align="right"
            />

            {/* Date Filter Dropdown */}
            <DateFilterDropdown
              value={dateFilter}
              onChange={setDateFilter}
              align="right"
            />

            {/* Platform / Vector Filter */}
            <div className="min-w-[150px]">
              <select
                value={selectedPlatform}
                onChange={(e) => setSelectedPlatform(e.target.value)}
                className="w-full px-3 py-2 text-xs font-semibold rounded-2xl bg-white border border-[#E2E1DC] text-brand-dark focus:outline-none focus:border-[#111312] cursor-pointer shadow-xs"
              >
                <option value="all">All Threat Types</option>
                <option value="phishing">Fake Websites</option>
                <option value="typosquat">Lookalike websites</option>
                <option value="social">Fake social accounts</option>
                <option value="mobile">Fake mobile apps</option>
              </select>
            </div>

            {/* Reset Filter Button */}
            {(threatFilter !== 'all' || dateFilter.preset !== '30d' || selectedPlatform !== 'all' || searchQuery.trim()) && (
              <button
                type="button"
                onClick={() => {
                  setSearchQuery('');
                  setThreatFilter('all');
                  setDateFilter({ preset: '30d', label: '30 days' });
                  setSelectedPlatform('all');
                }}
                className="inline-flex items-center gap-1 px-3 py-2 text-xs font-bold text-[#737478] hover:text-[#111312] transition-colors cursor-pointer"
                title="Reset all filters"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Reset</span>
              </button>
            )}
          </div>

        </div>
      </Card>

      {/* Threats Table */}
      <Card padding="none">
        <div className="p-4 border-b border-brand-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-brand-dark">Threats found</h3>
            <p className="text-xs text-brand-muted">Showing {filteredThreats.length} matching threat records</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-surface-light text-brand-muted border-b border-brand-border font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-6 py-3.5">Threat Target</th>
                <th className="px-6 py-3.5">Threat Type</th>
                <th className="px-6 py-3.5">Risk Level</th>
                <th className="px-6 py-3.5">First Detected</th>
                <th className="px-6 py-3.5">Current Status</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border/60">
              {filteredThreats.length > 0 ? (
                filteredThreats.map((threat) => {
                  const PlatformIcon = getPlatformIcon(threat.category);

                  const friendlyCategoryName = 
                    threat.category === 'typosquatting' ? 'Lookalike website' :
                    threat.category === 'social_impersonation' ? 'Fake social account' :
                    threat.category === 'executive_impersonation' ? 'Fake executive profile' :
                    threat.category === 'mobile_malware' ? 'Fake mobile app' :
                    threat.category === 'credential_harvesting' ? 'Password theft site' :
                    threat.category === 'scam_advertisement' ? 'Fake advertisement' :
                    'Fake website';

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

                      {/* Threat Type */}
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#F4F3EF] text-[#111312] font-semibold text-[11px] border border-[#DCDAD4]">
                          <PlatformIcon className="w-3.5 h-3.5 text-[#434346]" />
                          <span>{friendlyCategoryName}</span>
                        </span>
                      </td>

                      {/* Risk Level */}
                      <td className="px-6 py-4">
                        <div className="flex flex-col gap-1">
                          <div className="flex items-center gap-2">
                            <span className="font-extrabold text-brand-dark text-xs">{threat.riskScore}/100</span>
                            <Badge severity={threat.severity} size="sm" />
                          </div>
                          <div className="w-20 h-1.5 bg-brand-surface rounded-full overflow-hidden">
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

                      {/* Detected Date */}
                      <td className="px-6 py-4 text-brand-muted whitespace-nowrap text-[11px]">
                        {new Date(threat.firstSeenAt).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric'
                        })}
                      </td>

                      {/* Current Status */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge status={threat.status} size="sm" />
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
