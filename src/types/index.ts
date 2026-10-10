// Core TypeScript models for BrandShield AI

export type UserRole = 'brand_owner' | 'customer' | 'admin' | 'guest';

export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string;
  isPhoneVerified: boolean;
  role: UserRole;
  avatarUrl?: string;
  associatedBrandId?: string;
  createdAt: string;
}

export type ThreatSeverity = 'low' | 'medium' | 'high' | 'critical';

export type ThreatStatus = 
  | 'active'
  | 'under_investigation'
  | 'takedown_requested'
  | 'resolved'
  | 'false_positive';

export type ThreatCategory = 
  | 'phishing_website'
  | 'typosquatting'
  | 'social_impersonation'
  | 'executive_impersonation'
  | 'mobile_malware'
  | 'credential_harvesting'
  | 'scam_advertisement';

export type ThreatSource = 
  | 'customer_report'
  | 'automated_crawler'
  | 'threat_intelligence_feed'
  | 'dns_monitor'
  | 'ssl_transparency_log';

export interface ThreatEvidence {
  id: string;
  type: 'screenshot' | 'dom_diff' | 'whois' | 'ssl_cert' | 'logo_match' | 'scam_keywords';
  title: string;
  description: string;
  confidenceScore: number; // 0 - 100
  data: Record<string, any>;
  capturedAt: string;
  thumbnailUrl?: string;
}

export interface SuspiciousThreat {
  id: string;
  brandId: string;
  targetDomainOrUrl: string;
  category: ThreatCategory;
  severity: ThreatSeverity;
  status: ThreatStatus;
  source: ThreatSource;
  riskScore: number; // 0 - 100
  modelConfidence?: number; // 0 - 100
  scoringVersion: string;
  riskExplanation: string;
  domainSimilarityScore: number; // 0 - 100
  visualSimilarityScore: number; // 0 - 100
  logoSimilarityScore: number; // 0 - 100
  scamLanguageDetected: boolean;
  firstSeenAt: string;
  lastObservedAt: string;
  ipAddress?: string;
  hostingProvider?: string;
  registrar?: string;
  targetGeo?: string;
  reportedByCount: number;
  campaignId?: string;
  evidence: ThreatEvidence[];
  analystNotes?: string[];
  takedownStatus?: {
    requestedAt?: string;
    authorityContacted?: string;
    ticketId?: string;
    status: 'pending' | 'acknowledged' | 'approved' | 'rejected' | 'completed';
    estimatedResolution?: string;
  };
}

export interface BrandAsset {
  id: string;
  type: 'domain' | 'subdomain' | 'logo' | 'social_handle' | 'mobile_app' | 'trademark';
  value: string;
  status: 'verified' | 'pending' | 'failed' | 'expired';
  verifiedAt?: string;
  dnsTxtRecord?: string;
  metaTag?: string;
  healthStatus: 'secure' | 'warning' | 'critical';
}

export interface BrandProfile {
  id: string;
  name: string;
  legalEntityName: string;
  slug: string;
  industry: 'Banking & Fintech' | 'E-commerce & Retail' | 'Healthcare' | 'SaaS & Enterprise' | 'Crypto & Web3' | 'Telecommunications';
  officialWebsite: string;
  logoUrl: string;
  description: string;
  verificationStatus: 'verified' | 'pending' | 'additional_info_required' | 'rejected';
  verificationSubmittedAt: string;
  verifiedAt?: string;
  rejectionReason?: string;
  assets: BrandAsset[];
  trustScore: number; // 0 - 100
  totalThreatsNeutralized: number;
  activeMonitorsCount: number;
  customerRating: number; // 0 - 5
  reviewsCount: number;
}

export type ReportCategory = 
  | 'phishing_website'
  | 'fake_social_profile'
  | 'scam_sms_whatsapp'
  | 'rogue_mobile_app'
  | 'impersonation_email'
  | 'other';

export type CustomerReportStatus = 
  | 'submitted'
  | 'in_triage'
  | 'under_investigation'
  | 'takedown_initiated'
  | 'resolved'
  | 'rejected_not_threat';

export interface CustomerReport {
  id: string;
  reporterUserId?: string;
  reporterPhone?: string;
  brandId?: string;
  brandName?: string;
  category: ReportCategory;
  targetUrlOrIdentifier: string;
  description: string;
  evidenceFiles: Array<{
    id: string;
    filename: string;
    url: string;
    fileType: string;
    uploadedAt: string;
  }>;
  scamTactics: string[];
  status: CustomerReportStatus;
  submittedAt: string;
  updatedAt: string;
  resolutionNotes?: string;
  feedbackGivenByBrand?: string;
}

export interface VerifiedCustomerProof {
  type: 'invoice_receipt' | 'transaction_ref' | 'crypto_tx_or_order' | 'phone_otp_and_contract';
  referenceId: string;
  proofFileName: string;
  proofFileUrl?: string;
  verificationTimestamp: string;
  verificationStatus: 'verified_authentic' | 'under_review' | 'flagged';
  proofScore: number; // 0 - 100
  orderAmount?: string;
  productOrServicePurchased: string;
  cryptographicHash?: string;
}

export interface CustomerReview {
  id: string;
  brandId: string;
  brandName: string;
  userId: string;
  userName: string;
  userPhoneMasked?: string;
  isPhoneVerified: boolean;
  rating: number; // 1 to 5
  title: string;
  comment: string;
  createdAt: string;
  upvotesCount: number;
  isCustomerVerifiedOnly: boolean;
  verifiedProof: VerifiedCustomerProof;
  brandResponse?: {
    responderName: string;
    responderRole: string;
    response: string;
    respondedAt: string;
  };
}

export interface ThreatCampaign {
  id: string;
  brandId: string;
  name: string;
  threatActor?: string;
  detectedAt: string;
  severity: ThreatSeverity;
  status: 'active' | 'contained' | 'mitigated';
  summary: string;
  associatedThreatIds: string[];
  affectedCustomerCountEst: number;
  targetedRegions: string[];
  primaryAttackVectors: string[];
}

export interface SecurityAlert {
  id: string;
  brandId: string;
  title: string;
  message: string;
  severity: ThreatSeverity;
  category: ThreatCategory;
  threatId?: string;
  timestamp: string;
  isRead: boolean;
  actionUrl?: string;
}
