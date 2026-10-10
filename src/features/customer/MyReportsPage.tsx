import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { reportService } from '../../services/api';
import { CustomerReport } from '../../types';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { 
  FileCheck2, 
  Clock, 
  ShieldAlert, 
  Send, 
  CheckCircle2, 
  AlertTriangle, 
  Plus, 
  ExternalLink,
  ShieldCheck,
  Sparkles
} from 'lucide-react';

export const MyReportsPage: React.FC = () => {
  const { user } = useAuth();
  const [reports, setReports] = useState<CustomerReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      try {
        const data = await reportService.getReports(user?.id || 'user_cust_1');
        setReports(data);
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [user]);

  const timelineSteps = [
    { key: 'submitted', label: 'Submitted' },
    { key: 'in_triage', label: 'In Triage' },
    { key: 'under_investigation', label: 'Under Investigation' },
    { key: 'takedown_initiated', label: 'Takedown Initiated' },
    { key: 'resolved', label: 'Resolved / Takedown Complete' }
  ];

  const getStepIndex = (status: string) => {
    switch (status) {
      case 'submitted': return 0;
      case 'in_triage': return 1;
      case 'under_investigation': return 2;
      case 'takedown_initiated': return 3;
      case 'resolved': return 4;
      default: return 1;
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-brand-dark tracking-tight">My Threat Submissions Tracker</h1>
          <p className="text-xs text-brand-muted mt-1">
            Track live investigation updates, evidence triage milestones, and authoritative takedowns for your reports.
          </p>
        </div>

        <Link to="/customer/report">
          <Button leftIcon={<Plus className="w-4 h-4" />}>
            Report New Scam
          </Button>
        </Link>
      </div>

      {/* Reports List */}
      <div className="space-y-6">
        {reports.length > 0 ? (
          reports.map((report) => {
            const currentStepIdx = getStepIndex(report.status);

            return (
              <Card key={report.id} className="space-y-6">
                
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-brand-border/60">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-[#111312] uppercase">#{report.id}</span>
                      <span className="text-brand-muted text-xs">&bull;</span>
                      <h3 className="text-sm font-bold text-brand-dark">{report.brandName || 'Brand Target'}</h3>
                    </div>
                    <p className="font-mono text-xs text-brand-dark font-medium mt-1 truncate max-w-md">
                      {report.targetUrlOrIdentifier}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge status={report.status} />
                    <span className="text-[11px] text-brand-muted">
                      {new Date(report.submittedAt).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {/* Interactive Status Timeline */}
                <div className="p-4 sm:p-6 rounded-3xl bg-[#F8F7F4] border border-brand-border space-y-4">
                  <span className="text-[11px] font-bold text-brand-muted uppercase tracking-wider">Live Investigation Milestones</span>

                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 sm:gap-4 relative">
                    {timelineSteps.map((step, idx) => {
                      const isComplete = idx <= currentStepIdx;
                      const isCurrent = idx === currentStepIdx;

                      return (
                        <div key={step.key} className="flex flex-col items-center text-center space-y-1.5">
                          <div
                            className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                              isComplete
                                ? 'bg-emerald-600 text-white shadow-sm'
                                : 'bg-[#F4F3EF] text-brand-muted border border-brand-border'
                            }`}
                          >
                            {isComplete ? <CheckCircle2 className="w-4 h-4" /> : idx + 1}
                          </div>
                          <span className={`text-[10px] font-semibold leading-tight ${
                            isCurrent ? 'text-[#111312] font-bold' : isComplete ? 'text-brand-dark' : 'text-brand-muted'
                          }`}>
                            {step.label}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Customer Report Description & Tactics */}
                <div className="space-y-2 text-xs">
                  <span className="font-bold text-brand-muted uppercase text-[10px]">Your Submission Notes:</span>
                  <p className="text-brand-dark leading-relaxed">{report.description}</p>

                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {report.scamTactics.map((tactic, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded-md bg-[#F4F3EF] text-[#111312] text-[10px] font-bold border border-[#DCDAD4]">
                        {tactic}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Official Brand Resolution Note */}
                {report.resolutionNotes && (
                  <div className="p-4 rounded-2xl bg-white border border-brand-border shadow-sm space-y-1.5 border-l-4 border-l-emerald-600">
                    <div className="flex items-center gap-2 text-xs font-bold text-emerald-800">
                      <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      <span>Security Operations Resolution Update</span>
                    </div>
                    <p className="text-xs text-brand-dark leading-relaxed">
                      {report.resolutionNotes}
                    </p>
                  </div>
                )}
              </Card>
            );
          })
        ) : (
          <Card className="text-center py-12 space-y-3">
            <FileCheck2 className="w-12 h-12 text-brand-muted mx-auto" />
            <h3 className="text-base font-bold text-brand-dark">No Reports Submitted Yet</h3>
            <p className="text-xs text-brand-muted max-w-sm mx-auto">
              If you encounter a suspicious link or phishing SMS impersonating a trusted brand, submit a report here.
            </p>
            <Link to="/customer/report" className="inline-block pt-2">
              <Button size="sm">Submit Threat Report</Button>
            </Link>
          </Card>
        )}
      </div>

    </div>
  );
};
