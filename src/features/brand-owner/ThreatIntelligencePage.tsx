import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useBrand } from '../../context/BrandContext';
import { threatService } from '../../services/api';
import { SuspiciousThreat, ThreatSeverity, ThreatStatus } from '../../types';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { SearchInput } from '../../components/ui/Input';
import { 
  ShieldAlert, 
  Search, 
  Filter, 
  ArrowRight, 
  ExternalLink, 
  Send, 
  CheckCircle2, 
  Clock, 
  Globe2, 
  Eye, 
  Layers, 
  FileDown, 
  Sparkles,
  AlertOctagon
} from 'lucide-react';

export const ThreatIntelligencePage: React.FC = () => {
  const { currentBrand } = useBrand();
  const [threats, setThreats] = useState<SuspiciousThreat[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'cards' | 'table'>('cards');
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const loadThreats = async () => {
      setIsLoading(true);
      try {
        const data = await threatService.getThreats(currentBrand?.id);
        setThreats(data);
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    loadThreats();
  }, [currentBrand]);

  const filteredThreats = threats.filter((threat) => {
    const matchesSearch = 
      threat.targetDomainOrUrl.toLowerCase().includes(searchQuery.toLowerCase()) ||
      threat.riskExplanation.toLowerCase().includes(searchQuery.toLowerCase()) ||
      threat.category.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesSeverity = severityFilter === 'all' || threat.severity === severityFilter;
    const matchesStatus = statusFilter === 'all' || threat.status === statusFilter;

    return matchesSearch && matchesSeverity && matchesStatus;
  });

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Top Title & Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-brand-dark tracking-tight">Threat Intelligence Workspace</h1>
          <p className="text-xs text-brand-muted mt-1">
            Real-time detection engine for spoofed domains, phishing kits, rogue APKs, and executive impersonation.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link to="/brand-owner/reports">
            <Button variant="outline" size="sm" leftIcon={<FileDown className="w-4 h-4" />}>
              Export Threat Feed
            </Button>
          </Link>
          <div className="flex bg-[#F8F7F4] p-1 rounded-2xl border border-brand-border">
            <button
              onClick={() => setViewMode('cards')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                viewMode === 'cards' ? 'bg-[#111312] text-white shadow-sm' : 'text-brand-muted hover:text-brand-dark'
              }`}
            >
              Cards
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                viewMode === 'table' ? 'bg-[#111312] text-white shadow-sm' : 'text-brand-muted hover:text-brand-dark'
              }`}
            >
              Table
            </button>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <Card padding="sm">
        <div className="flex flex-col md:flex-row items-center gap-3">
          <div className="w-full md:flex-1">
            <SearchInput
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search candidate domain, URL, IP, or threat keyword..."
            />
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
            {/* Severity Filter */}
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="rounded-2xl bg-brand-surface-light border border-brand-border px-3 py-2 text-xs font-semibold text-brand-dark focus:outline-none focus:border-[#111312]"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-2xl bg-brand-surface-light border border-brand-border px-3 py-2 text-xs font-semibold text-brand-dark focus:outline-none focus:border-[#111312]"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active Threats</option>
              <option value="under_investigation">Under Investigation</option>
              <option value="takedown_requested">Takedown Requested</option>
              <option value="resolved">Resolved</option>
              <option value="false_positive">False Positive</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Threat List (Cards View) */}
      {viewMode === 'cards' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredThreats.map((threat) => (
            <Card
              key={threat.id}
              hoverEffect
              onClick={() => navigate(`/brand-owner/threats/${threat.id}`)}
              className="flex flex-col justify-between group space-y-4"
            >
              <div className="space-y-3">
                {/* Header: Status and Severity */}
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-2">
                    <Badge severity={threat.severity} />
                    <Badge status={threat.status} />
                  </div>
                  <span className="text-[11px] text-brand-muted font-medium">
                    First seen: {new Date(threat.firstSeenAt).toLocaleDateString()}
                  </span>
                </div>

                {/* Threat URL / Target */}
                <div>
                  <h3 className="text-sm font-extrabold text-brand-dark font-mono truncate group-hover:text-[#111312] group-hover:underline transition-colors">
                    {threat.targetDomainOrUrl}
                  </h3>
                  <p className="text-xs text-brand-muted mt-1 leading-relaxed line-clamp-2">
                    {threat.riskExplanation}
                  </p>
                </div>

                {/* Similarity & AI Markers */}
                <div className="grid grid-cols-3 gap-2 p-3 rounded-2xl bg-brand-surface-light border border-brand-border text-center">
                  <div>
                    <span className="text-[10px] font-bold text-brand-muted uppercase">Domain Sim.</span>
                    <p className="text-xs font-bold text-brand-dark">{threat.domainSimilarityScore}%</p>
                  </div>
                  <div>
                    <span className="text-[10px] font-bold text-brand-muted uppercase">Logo Match</span>
                    <p className="text-xs font-bold text-brand-dark">{threat.logoSimilarityScore}%</p>
                  </div>
                  <div>
                    <span className="text-[10px] font-bold text-brand-muted uppercase">Visual UI</span>
                    <p className="text-xs font-bold text-brand-dark">{threat.visualSimilarityScore}%</p>
                  </div>
                </div>
              </div>

              {/* Footer with Risk Score Pill & Action */}
              <div className="pt-3 border-t border-brand-border/60 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`px-2.5 py-1 rounded-xl text-xs font-extrabold ${
                    threat.riskScore >= 90 ? 'bg-red-50 text-[#8A1C2E] border border-red-200' :
                    threat.riskScore >= 70 ? 'bg-rose-50 text-rose-700 border border-rose-200' :
                    threat.riskScore >= 40 ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                    'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  }`}>
                    Risk Score: {threat.riskScore}/100
                  </div>
                  <span className="text-[10px] text-brand-muted capitalize">
                    Source: {threat.source.replace(/_/g, ' ')}
                  </span>
                </div>

                <Button variant="secondary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                  Inspect Evidence
                </Button>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        /* Table View */
        <Card padding="none">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-brand-surface-light text-brand-muted border-b border-brand-border font-semibold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-6 py-3.5">Target</th>
                  <th className="px-6 py-3.5">Category</th>
                  <th className="px-6 py-3.5">Risk Score</th>
                  <th className="px-6 py-3.5">Severity</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Source</th>
                  <th className="px-6 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border/60">
                {filteredThreats.map((threat) => (
                  <tr key={threat.id} className="hover:bg-brand-surface-light/40 transition-colors">
                    <td className="px-6 py-4 font-mono font-medium text-brand-dark max-w-xs truncate">
                      {threat.targetDomainOrUrl}
                    </td>
                    <td className="px-6 py-4 text-brand-muted capitalize">
                      {threat.category.replace(/_/g, ' ')}
                    </td>
                    <td className="px-6 py-4 font-bold text-brand-dark">
                      {threat.riskScore} / 100
                    </td>
                    <td className="px-6 py-4">
                      <Badge severity={threat.severity} />
                    </td>
                    <td className="px-6 py-4">
                      <Badge status={threat.status} />
                    </td>
                    <td className="px-6 py-4 text-brand-muted capitalize text-[11px]">
                      {threat.source.replace(/_/g, ' ')}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link to={`/brand-owner/threats/${threat.id}`}>
                        <Button variant="secondary" size="sm">
                          Inspect
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

    </div>
  );
};
