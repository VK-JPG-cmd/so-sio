import { SuspiciousThreat, ThreatStatus, ThreatCampaign, SecurityAlert } from '../../types';
import { MOCK_THREATS, MOCK_CAMPAIGNS, MOCK_ALERTS } from '../mockData';
import { apiClient } from './client';

const THREATS_STORAGE_KEY = 'brandshield_threats_data';
const CAMPAIGNS_STORAGE_KEY = 'brandshield_campaigns_data';
const ALERTS_STORAGE_KEY = 'brandshield_alerts_data';

export const threatService = {
  getThreats: async (brandId?: string): Promise<SuspiciousThreat[]> => {
    if (!apiClient.isMockMode) {
      try {
        return await apiClient.request<SuspiciousThreat[]>('/threats', {
          params: brandId ? { brandId } : undefined
        });
      } catch (err) {
        console.warn('Falling back to local threats store', err);
      }
    }

    const stored = localStorage.getItem(THREATS_STORAGE_KEY);
    let threats: SuspiciousThreat[] = stored ? JSON.parse(stored) : MOCK_THREATS;
    if (brandId) {
      threats = threats.filter(t => t.brandId === brandId);
    }
    return threats;
  },

  getThreatById: async (threatId: string): Promise<SuspiciousThreat | null> => {
    const threats = await threatService.getThreats();
    return threats.find(t => t.id === threatId) || null;
  },

  updateThreatStatus: async (threatId: string, status: ThreatStatus, note?: string): Promise<SuspiciousThreat> => {
    if (!apiClient.isMockMode) {
      try {
        return await apiClient.request<SuspiciousThreat>(`/threats/${threatId}/status`, {
          method: 'PATCH',
          body: JSON.stringify({ status, note })
        });
      } catch (err) {
        console.warn('Falling back to local threat status update', err);
      }
    }

    const threats = await threatService.getThreats();
    const threat = threats.find(t => t.id === threatId);
    if (!threat) throw new Error('Threat not found');

    threat.status = status;
    if (note) {
      threat.analystNotes = threat.analystNotes || [];
      threat.analystNotes.unshift(`[${new Date().toLocaleTimeString()}] Status changed to ${status}: ${note}`);
    }
    if (status === 'takedown_requested' && !threat.takedownStatus) {
      threat.takedownStatus = {
        requestedAt: new Date().toISOString(),
        authorityContacted: 'Domain Registrar & Hosting Abuse Team',
        ticketId: `BS-TK-${Math.floor(100000 + Math.random() * 900000)}`,
        status: 'pending',
        estimatedResolution: '4-12 hours'
      };
    } else if (status === 'resolved' && threat.takedownStatus) {
      threat.takedownStatus.status = 'completed';
    }

    localStorage.setItem(THREATS_STORAGE_KEY, JSON.stringify(threats));
    return threat;
  },

  requestTakedown: async (threatId: string, authorityNotes?: string): Promise<SuspiciousThreat> => {
    return threatService.updateThreatStatus(
      threatId, 
      'takedown_requested', 
      authorityNotes || 'Automated takedown request package dispatched to registrar abuse desk.'
    );
  },

  addAnalystNote: async (threatId: string, note: string): Promise<SuspiciousThreat> => {
    const threats = await threatService.getThreats();
    const threat = threats.find(t => t.id === threatId);
    if (!threat) throw new Error('Threat not found');

    threat.analystNotes = threat.analystNotes || [];
    threat.analystNotes.unshift(`[${new Date().toLocaleTimeString()}] Analyst Note: ${note}`);
    localStorage.setItem(THREATS_STORAGE_KEY, JSON.stringify(threats));
    return threat;
  },

  getCampaigns: async (brandId?: string): Promise<ThreatCampaign[]> => {
    if (!apiClient.isMockMode && brandId) {
      try {
        const rawCampaigns = await apiClient.request<any[]>(`/owner/brands/${brandId}/campaigns`);
        if (Array.isArray(rawCampaigns) && rawCampaigns.length > 0) {
          return rawCampaigns.map((c: any) => ({
            id: c.id,
            brandId: c.brand_id || brandId,
            name: c.title || 'Correlated Threat Campaign',
            threatActor: 'Fin7 / SilentShadow Threat Cluster',
            detectedAt: c.created_at || new Date().toISOString(),
            severity: (c.risk_score >= 80 ? 'critical' : c.risk_score >= 50 ? 'high' : 'medium') as any,
            status: (c.status?.toLowerCase() === 'active' ? 'active' : 'contained') as any,
            summary: c.description || 'Coordinated multi-vector campaign identified by BrandShield AI.',
            associatedThreatIds: ['threat_apex_01', 'threat_apex_02'],
            affectedCustomerCountEst: 1400,
            targetedRegions: ['United States', 'Canada', 'United Kingdom'],
            primaryAttackVectors: ['Smishing (SMS Lures)', 'Domain Typosquatting', 'Trojanized APK Overlay']
          }));
        }
      } catch (err) {
        console.warn('Falling back to local campaigns store', err);
      }
    }

    const stored = localStorage.getItem(CAMPAIGNS_STORAGE_KEY);
    let campaigns: ThreatCampaign[] = stored ? JSON.parse(stored) : MOCK_CAMPAIGNS;
    if (brandId) {
      campaigns = campaigns.filter(c => c.brandId === brandId);
    }
    return campaigns;
  },

  getAlerts: async (brandId?: string): Promise<SecurityAlert[]> => {
    const stored = localStorage.getItem(ALERTS_STORAGE_KEY);
    let alerts: SecurityAlert[] = stored ? JSON.parse(stored) : MOCK_ALERTS;
    if (brandId) {
      alerts = alerts.filter(a => a.brandId === brandId);
    }
    return alerts;
  },

  markAlertRead: async (alertId: string): Promise<void> => {
    const alerts = await threatService.getAlerts();
    const alert = alerts.find(a => a.id === alertId);
    if (alert) {
      alert.isRead = true;
      localStorage.setItem(ALERTS_STORAGE_KEY, JSON.stringify(alerts));
    }
  },

  analyzeUrl: async (url: string, brandId?: string): Promise<any> => {
    return await apiClient.request<any>('/analyze/url', {
      method: 'POST',
      body: JSON.stringify({ url, brand_id: brandId })
    });
  }
};

