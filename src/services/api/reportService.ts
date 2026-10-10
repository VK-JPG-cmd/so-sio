import { CustomerReport, CustomerReportStatus } from '../../types';
import { MOCK_REPORTS } from '../mockData';
import { apiClient } from './client';

const REPORTS_STORAGE_KEY = 'brandshield_customer_reports';

export const reportService = {
  getReports: async (userId?: string, brandId?: string): Promise<CustomerReport[]> => {
    if (!apiClient.isMockMode) {
      try {
        const rawReports = await apiClient.request<any[]>('/threat-reports/me');
        if (Array.isArray(rawReports) && rawReports.length > 0) {
          return rawReports.map((r: any) => ({
            id: r.id,
            reporterUserId: r.reporter_id || userId || 'user_cust_1',
            reporterPhone: '+1 (555) 902-1144',
            brandId: r.brand_id,
            brandName: 'ApexBank Global',
            category: (r.target_type?.toLowerCase() === 'domain' ? 'phishing_website' : 'fake_social_profile') as any,
            targetUrlOrIdentifier: r.target_value,
            description: r.description,
            evidenceFiles: [],
            scamTactics: ['Impersonation', 'Credential Harvesting'],
            status: (r.status?.toLowerCase() === 'confirmed' ? 'takedown_initiated' : 'under_investigation') as any,
            submittedAt: r.created_at || new Date().toISOString(),
            updatedAt: r.created_at || new Date().toISOString(),
          }));
        }
      } catch (err) {
        console.warn('Falling back to local customer reports', err);
      }
    }

    const stored = localStorage.getItem(REPORTS_STORAGE_KEY);
    let reports: CustomerReport[] = stored ? JSON.parse(stored) : MOCK_REPORTS;
    
    if (userId) {
      reports = reports.filter(r => r.reporterUserId === userId);
    }
    if (brandId) {
      reports = reports.filter(r => r.brandId === brandId);
    }
    return reports;
  },

  getReportById: async (reportId: string): Promise<CustomerReport | null> => {
    const reports = await reportService.getReports();
    return reports.find(r => r.id === reportId) || null;
  },

  submitReport: async (reportData: Partial<CustomerReport>): Promise<CustomerReport> => {
    if (!apiClient.isMockMode) {
      try {
        const targetTypeMap: Record<string, string> = {
          phishing_website: 'URL',
          fake_social_profile: 'SOCIAL_PROFILE',
          scam_sms_whatsapp: 'SMS_TEXT',
          rogue_mobile_app: 'MOBILE_APP',
          impersonation_email: 'URL'
        };
        const payload: any = {
          target_type: targetTypeMap[reportData.category || 'phishing_website'] || 'URL',
          target_value: reportData.targetUrlOrIdentifier || 'https://unknown-link.example',
          description: (reportData.description && reportData.description.length >= 10)
            ? reportData.description
            : 'Suspicious digital threat reported by user for threat intelligence triage.'
        };
        if (reportData.brandId && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(reportData.brandId)) {
          payload.brand_id = reportData.brandId;
        }

        const res = await apiClient.request<any>('/threat-reports', {
          method: 'POST',
          body: JSON.stringify(payload)
        });

        if (res && res.id) {
          return {
            id: res.id,
            reporterUserId: res.reporter_user_id || reportData.reporterUserId || 'cust_1',
            reporterPhone: reportData.reporterPhone || '+1 (555) 902-1144',
            brandId: res.brand_id || reportData.brandId,
            brandName: reportData.brandName || 'Target Brand',
            category: reportData.category || 'phishing_website',
            targetUrlOrIdentifier: res.target_value || reportData.targetUrlOrIdentifier || '',
            description: res.description || reportData.description || '',
            evidenceFiles: reportData.evidenceFiles || [],
            scamTactics: reportData.scamTactics || ['Phishing URL', 'Impersonation'],
            status: 'under_investigation',
            submittedAt: res.created_at || new Date().toISOString(),
            updatedAt: res.created_at || new Date().toISOString()
          };
        }
      } catch (err) {
        console.warn('Falling back to local report submission', err);
      }
    }

    await new Promise(r => setTimeout(r, 600));
    const reports = await reportService.getReports();
    const newReport: CustomerReport = {
      id: `rep_${Date.now()}`,
      reporterUserId: reportData.reporterUserId || 'user_cust_1',
      reporterPhone: reportData.reporterPhone || '+1 (555) 902-1144',
      brandId: reportData.brandId,
      brandName: reportData.brandName || 'Target Brand',
      category: reportData.category || 'phishing_website',
      targetUrlOrIdentifier: reportData.targetUrlOrIdentifier || 'https://unknown-link.example',
      description: reportData.description || 'Customer reported deceptive link.',
      evidenceFiles: reportData.evidenceFiles || [],
      scamTactics: reportData.scamTactics || ['Phishing URL', 'Impersonation'],
      status: 'submitted',
      submittedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      resolutionNotes: 'Report queued for automated brand triage and analyst verification.'
    };

    const updated = [newReport, ...reports];
    localStorage.setItem(REPORTS_STORAGE_KEY, JSON.stringify(updated));
    return newReport;
  },

  updateReportStatus: async (reportId: string, status: CustomerReportStatus, resolutionNotes?: string): Promise<CustomerReport> => {
    const reports = await reportService.getReports();
    const report = reports.find(r => r.id === reportId);
    if (!report) throw new Error('Report not found');

    report.status = status;
    report.updatedAt = new Date().toISOString();
    if (resolutionNotes) {
      report.resolutionNotes = resolutionNotes;
    }
    localStorage.setItem(REPORTS_STORAGE_KEY, JSON.stringify(reports));
    return report;
  }
};
