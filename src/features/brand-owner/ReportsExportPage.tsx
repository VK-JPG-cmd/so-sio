import React, { useState } from 'react';
import { useBrand } from '../../context/BrandContext';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { useNotification } from '../../context/NotificationContext';
import { 
  FileText, 
  Download, 
  FileDown, 
  Printer, 
  Calendar, 
  CheckCircle2, 
  ShieldCheck,
  Sparkles,
  ShieldAlert,
  Crosshair,
  TrendingUp,
  AlertOctagon
} from 'lucide-react';

export const ReportsExportPage: React.FC = () => {
  const { currentBrand } = useBrand();
  const { showToast } = useNotification();
  const [reportType, setReportType] = useState('executive');
  const [dateRange, setDateRange] = useState('30d');
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerateReport = (format: 'pdf' | 'csv' | 'json') => {
    setIsGenerating(true);
    setTimeout(() => {
      setIsGenerating(false);
      showToast({ 
        type: 'success', 
        title: `Report Ready (${format.toUpperCase()})`, 
        message: `BrandShield digital risk report for ${currentBrand?.name || 'ApexBank'} exported successfully.` 
      });

      if (format === 'pdf') {
        window.print();
      }
    }, 800);
  };

  // Real report statistics
  const threatsDetected = 142;
  const criticalThreats = 4;
  const campaignsIdentified = 3;
  const resolvedThreats = 138;

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-brand-dark tracking-tight">Reports & Compliance</h1>
          <p className="text-xs text-brand-muted mt-1">
            Generate executive digital risk summaries, takedown audit trails, and export verifiable threat intelligence dossiers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleGenerateReport('csv')}
            isLoading={isGenerating}
            leftIcon={<Download className="w-4 h-4" />}
          >
            Export CSV Feed
          </Button>

          <Button
            size="sm"
            onClick={() => handleGenerateReport('pdf')}
            isLoading={isGenerating}
            leftIcon={<Printer className="w-4 h-4" />}
          >
            Print / Save PDF Report
          </Button>
        </div>
      </div>

      {/* Report Controls Card */}
      <Card className="space-y-6">
        <div>
          <h3 className="text-sm font-bold text-brand-dark">Configure Report Parameters</h3>
          <p className="text-xs text-brand-muted">Select scope, timeframe, and output format.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-brand-dark mb-1.5">Report Scope</label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full rounded-2xl bg-brand-surface-light border border-brand-border px-4 py-2.5 text-xs font-bold text-brand-dark focus:outline-none focus:border-[#111312]"
            >
              <option value="executive">Executive Summary (Board of Directors & C-Suite)</option>
              <option value="technical">Technical Threat & IOC Archive (Security Team)</option>
              <option value="takedown">Registrar Takedown Audit Log (Legal & Compliance)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-brand-dark mb-1.5">Time Period</label>
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="w-full rounded-2xl bg-brand-surface-light border border-brand-border px-4 py-2.5 text-xs font-bold text-brand-dark focus:outline-none focus:border-[#111312]"
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last Quarter (90 Days)</option>
              <option value="ytd">Year to Date (2026)</option>
            </select>
          </div>
        </div>

        {/* Live Digital Risk Summary Document View */}
        <div className="p-6 sm:p-8 rounded-3xl bg-white border border-brand-border shadow-soft space-y-6">
          
          {/* Document Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-brand-border">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-[#111312] text-[#FBF5A5] flex items-center justify-center border border-[#2B2D2C]">
                <FileText className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-base font-extrabold text-brand-dark">BrandShield Digital Risk Summary</h4>
                <p className="text-xs text-brand-muted">
                  Protected Entity: <strong className="text-brand-dark">{currentBrand?.name || 'ApexBank Global'}</strong> &bull; Report Period: Last {dateRange.toUpperCase()}
                </p>
              </div>
            </div>

            <span className="px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 font-bold text-xs border border-emerald-200 self-start sm:self-auto">
              ✓ Verified Compliance Dossier
            </span>
          </div>

          {/* 5 Core Required Metrics in Report */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl bg-brand-surface-light border border-brand-border">
              <span className="text-[10px] font-bold text-brand-muted uppercase tracking-wider block">Threats Detected</span>
              <p className="text-2xl font-extrabold text-brand-dark mt-1">{threatsDetected}</p>
              <p className="text-[10px] text-brand-muted mt-0.5">All vectors identified</p>
            </div>

            <div className="p-4 rounded-2xl bg-rose-50/70 border border-rose-200">
              <span className="text-[10px] font-bold text-rose-800 uppercase tracking-wider block">Critical Threats</span>
              <p className="text-2xl font-extrabold text-rose-900 mt-1">{criticalThreats}</p>
              <p className="text-[10px] text-rose-700 mt-0.5">High-impact phishing</p>
            </div>

            <div className="p-4 rounded-2xl bg-[#F4F3EF] border border-[#DCDAD4]">
              <span className="text-[10px] font-bold text-[#111312] uppercase tracking-wider block">Campaigns Identified</span>
              <p className="text-2xl font-extrabold text-[#111312] mt-1">{campaignsIdentified}</p>
              <p className="text-[10px] text-[#434346] mt-0.5">Coordinated fraud clusters</p>
            </div>

            <div className="p-4 rounded-2xl bg-emerald-50/70 border border-emerald-200">
              <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider block">Resolved Threats</span>
              <p className="text-2xl font-extrabold text-emerald-900 mt-1">{resolvedThreats}</p>
              <p className="text-[10px] text-emerald-700 mt-0.5">97.2% takedown success</p>
            </div>
          </div>

          {/* Executive Risk Trends Summary Block */}
          <div className="p-4 rounded-2xl bg-brand-surface-light border border-brand-border space-y-2 text-xs">
            <div className="flex items-center gap-2 font-bold text-brand-dark">
              <TrendingUp className="w-4 h-4 text-rose-500" />
              <span>Risk Trends & Threat Vector Trajectory</span>
            </div>
            <p className="text-brand-muted leading-relaxed">
              Overall brand risk has seen a <strong>+4.2% trajectory</strong> over the recent observation window, driven predominantly by domain typosquatting and fake social customer service profiles. 
              Active enforcement protocols have successfully neutralized <strong>138 threats</strong> with an average resolution turnaround of 4.2 hours.
            </p>
          </div>

          {/* Perimeter Summary */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs pt-2">
            <div className="p-3.5 rounded-2xl bg-white border border-brand-border">
              <span className="font-bold text-brand-dark block mb-1">Protected Perimeter Scope</span>
              <ul className="space-y-1 text-brand-muted text-[11px]">
                <li>• Official Domain: {currentBrand?.officialWebsite}</li>
                <li>• Verified Brand Assets: {currentBrand?.assets.length || 5} Monitored Properties</li>
                <li>• Trust & Safety Rating: {currentBrand?.trustScore || 98}% Overall Consumer Trust</li>
              </ul>
            </div>

            <div className="p-3.5 rounded-2xl bg-white border border-brand-border">
              <span className="font-bold text-brand-dark block mb-1">Compliance & Audit Sign-Off</span>
              <p className="text-brand-muted text-[11px] leading-relaxed">
                This report is compiled in accordance with standard automated brand intelligence and trademark defense guidelines.
              </p>
            </div>
          </div>

        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-end gap-3 pt-2">
          <Button
            variant="outline"
            onClick={() => handleGenerateReport('json')}
            isLoading={isGenerating}
            leftIcon={<Download className="w-4 h-4" />}
          >
            Export Raw JSON
          </Button>

          <Button
            variant="outline"
            onClick={() => handleGenerateReport('csv')}
            isLoading={isGenerating}
            leftIcon={<Download className="w-4 h-4" />}
          >
            Export CSV Feed
          </Button>

          <Button
            onClick={() => handleGenerateReport('pdf')}
            isLoading={isGenerating}
            leftIcon={<Printer className="w-4 h-4" />}
          >
            Generate & Print PDF Dossier
          </Button>
        </div>
      </Card>

    </div>
  );
};
