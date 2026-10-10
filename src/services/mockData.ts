import { 
  BrandProfile, 
  SuspiciousThreat, 
  CustomerReport, 
  CustomerReview, 
  ThreatCampaign, 
  SecurityAlert,
  User
} from '../types';

export const MOCK_USERS: User[] = [
  {
    id: 'user_bo_1',
    name: 'Elena Rostova',
    email: 'elena.rostova@apexbank.com',
    phone: '+1 (555) 382-9912',
    isPhoneVerified: true,
    role: 'brand_owner',
    avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
    associatedBrandId: 'brand_apex_bank',
    createdAt: '2026-01-15T09:00:00Z',
  },
  {
    id: 'user_cust_1',
    name: 'David Chen',
    email: 'david.chen@gmail.com',
    phone: '+1 (555) 902-1144',
    isPhoneVerified: true,
    role: 'customer',
    avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80',
    createdAt: '2026-02-10T14:22:00Z',
  },
  {
    id: 'user_cust_2',
    name: 'Sarah Jenkins',
    email: 'sarah.j@outlook.com',
    phone: '+1 (555) 774-8821',
    isPhoneVerified: true,
    role: 'customer',
    avatarUrl: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80',
    createdAt: '2026-03-01T11:15:00Z',
  }
];

export const MOCK_BRANDS: BrandProfile[] = [
  {
    id: 'brand_apex_bank',
    name: 'ApexBank Global',
    legalEntityName: 'Apex Financial Services Inc.',
    slug: 'apex-bank',
    industry: 'Banking & Fintech',
    officialWebsite: 'https://apexbank.com',
    logoUrl: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=120&auto=format&fit=crop&q=80',
    description: 'Premier digital banking and wealth management services with enterprise-grade security.',
    verificationStatus: 'verified',
    verificationSubmittedAt: '2026-01-10T10:00:00Z',
    verifiedAt: '2026-01-12T15:30:00Z',
    trustScore: 98,
    totalThreatsNeutralized: 142,
    activeMonitorsCount: 38,
    customerRating: 4.8,
    reviewsCount: 320,
    assets: [
      {
        id: 'asset_1',
        type: 'domain',
        value: 'apexbank.com',
        status: 'verified',
        verifiedAt: '2026-01-12T15:30:00Z',
        dnsTxtRecord: 'brandshield-verification=apex-bv7829-token',
        healthStatus: 'secure',
      },
      {
        id: 'asset_2',
        type: 'domain',
        value: 'online.apexbank.com',
        status: 'verified',
        verifiedAt: '2026-01-12T16:00:00Z',
        dnsTxtRecord: 'brandshield-verification=apex-bv7829-token',
        healthStatus: 'secure',
      },
      {
        id: 'asset_3',
        type: 'social_handle',
        value: '@ApexBankOfficial (Twitter/X)',
        status: 'verified',
        verifiedAt: '2026-01-14T11:00:00Z',
        healthStatus: 'secure',
      },
      {
        id: 'asset_4',
        type: 'mobile_app',
        value: 'com.apexbank.mobile (iOS & Android)',
        status: 'verified',
        verifiedAt: '2026-01-15T08:00:00Z',
        healthStatus: 'secure',
      },
      {
        id: 'asset_5',
        type: 'logo',
        value: 'Official Apex Prismatic Hexagon Logo (SHA-256 Hash: 9f8a3c42)',
        status: 'verified',
        verifiedAt: '2026-01-12T15:30:00Z',
        healthStatus: 'secure',
      }
    ]
  },
  {
    id: 'brand_lumina',
    name: 'Lumina Cloud',
    legalEntityName: 'Lumina Systems Corp',
    slug: 'lumina-cloud',
    industry: 'SaaS & Enterprise',
    officialWebsite: 'https://luminacloud.io',
    logoUrl: 'https://images.unsplash.com/photo-1633409381658-a0c217e6e87f?w=120&auto=format&fit=crop&q=80',
    description: 'AI-native developer infrastructure and cloud orchestration.',
    verificationStatus: 'verified',
    verificationSubmittedAt: '2026-02-01T08:00:00Z',
    verifiedAt: '2026-02-03T12:00:00Z',
    trustScore: 95,
    totalThreatsNeutralized: 67,
    activeMonitorsCount: 19,
    customerRating: 4.9,
    reviewsCount: 184,
    assets: [
      {
        id: 'asset_l1',
        type: 'domain',
        value: 'luminacloud.io',
        status: 'verified',
        verifiedAt: '2026-02-03T12:00:00Z',
        dnsTxtRecord: 'brandshield-verification=lumina-vx9911',
        healthStatus: 'secure',
      }
    ]
  },
  {
    id: 'brand_aurapay',
    name: 'AuraPay Checkout',
    legalEntityName: 'Aura Financial Technologies',
    slug: 'aurapay',
    industry: 'Banking & Fintech',
    officialWebsite: 'https://aurapay.me',
    logoUrl: 'https://images.unsplash.com/photo-1557804506-669a67965ba0?w=120&auto=format&fit=crop&q=80',
    description: 'One-click checkout and seamless cross-border consumer payment gateway.',
    verificationStatus: 'verified',
    verificationSubmittedAt: '2026-02-15T14:00:00Z',
    verifiedAt: '2026-02-17T09:30:00Z',
    trustScore: 92,
    totalThreatsNeutralized: 89,
    activeMonitorsCount: 24,
    customerRating: 4.6,
    reviewsCount: 412,
    assets: [
      {
        id: 'asset_a1',
        type: 'domain',
        value: 'aurapay.me',
        status: 'verified',
        verifiedAt: '2026-02-17T09:30:00Z',
        dnsTxtRecord: 'brandshield-verification=aura-px4421',
        healthStatus: 'secure',
      }
    ]
  },
  {
    id: 'brand_novashop',
    name: 'Nova Market',
    legalEntityName: 'Nova Commerce LLC',
    slug: 'nova-market',
    industry: 'E-commerce & Retail',
    officialWebsite: 'https://novamarket.store',
    logoUrl: 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=120&auto=format&fit=crop&q=80',
    description: 'Curated organic lifestyle and sustainable direct-to-consumer goods.',
    verificationStatus: 'pending',
    verificationSubmittedAt: '2026-10-08T18:00:00Z',
    trustScore: 84,
    totalThreatsNeutralized: 12,
    activeMonitorsCount: 8,
    customerRating: 4.4,
    reviewsCount: 78,
    assets: [
      {
        id: 'asset_n1',
        type: 'domain',
        value: 'novamarket.store',
        status: 'pending',
        dnsTxtRecord: 'brandshield-verification=nova-nv2026-check',
        healthStatus: 'warning',
      }
    ]
  }
];

export const MOCK_THREATS: SuspiciousThreat[] = [
  {
    id: 'threat_apex_01',
    brandId: 'brand_apex_bank',
    targetDomainOrUrl: 'https://apex-bank-secure-login.net/verify',
    category: 'phishing_website',
    severity: 'critical',
    status: 'active',
    source: 'automated_crawler',
    riskScore: 96,
    modelConfidence: 94,
    scoringVersion: 'RiskGuard-v4.2.1-hybrid',
    riskExplanation: 'Cloned login portal with deceptive domain structure, harvested credentials form, and 94% visual similarity to official ApexBank online portal.',
    domainSimilarityScore: 89,
    visualSimilarityScore: 94,
    logoSimilarityScore: 98,
    scamLanguageDetected: true,
    firstSeenAt: '2026-10-09T04:12:00Z',
    lastObservedAt: '2026-10-09T18:40:00Z',
    ipAddress: '185.220.101.44',
    hostingProvider: 'HostWinds Bulletproof VPS',
    registrar: 'NameCheap Privacy Guard Inc.',
    targetGeo: 'North America / EU',
    reportedByCount: 14,
    campaignId: 'camp_01',
    analystNotes: [
      'Automated crawler intercepted live HTTP POST submission targeting /api/harvest-token endpoint.',
      'SSL cert issued via Let\'s Encrypt 18 hours ago.',
      'Takedown abuse notification drafted and dispatched to NameCheap Abuse Desk.'
    ],
    takedownStatus: {
      requestedAt: '2026-10-09T08:00:00Z',
      authorityContacted: 'NameCheap Abuse Desk & Cloudflare Trust & Safety',
      ticketId: 'NC-ABUSE-994182',
      status: 'pending',
      estimatedResolution: '4-8 hours'
    },
    evidence: [
      {
        id: 'ev_1',
        type: 'logo_match',
        title: 'Unauthorized Brand Logo Extraction',
        description: 'Exact pixel clone of ApexBank vector SVG badge detected in HTML `<header>` node with identical color hex values.',
        confidenceScore: 98,
        capturedAt: '2026-10-09T04:15:00Z',
        data: {
          matchedHash: '9f8a3c42',
          similarityPercent: 98.4,
          tamperedElements: ['Stripped trademark notice', 'Inline SVG recolored stroke']
        }
      },
      {
        id: 'ev_2',
        type: 'scam_keywords',
        title: 'Social Engineering & Urgency NLP Markers',
        description: 'Scam engine flagged urgent coercions: "Your account is temporarily locked! Enter 2FA passcode immediately to avoid total asset freeze within 15 minutes."',
        confidenceScore: 96,
        capturedAt: '2026-10-09T04:15:00Z',
        data: {
          nlpKeywords: ['Account Locked', 'Urgent 2FA Passcode', 'Immediate Asset Freeze', '15 Minutes Remaining'],
          urgencyScore: 9.6
        }
      },
      {
        id: 'ev_3',
        type: 'ssl_cert',
        title: 'Ephemeral Free SSL Certificate',
        description: 'Domain registered 22 hours ago using newly generated wildcard cert with high-entropy subdomain routing.',
        confidenceScore: 91,
        capturedAt: '2026-10-09T04:16:00Z',
        data: {
          issuer: 'Let\'s Encrypt Authority X3',
          validFrom: '2026-10-08T22:00:00Z',
          sanDomains: ['apex-bank-secure-login.net', '*.apex-bank-secure-login.net']
        }
      }
    ]
  },
  {
    id: 'threat_apex_02',
    brandId: 'brand_apex_bank',
    targetDomainOrUrl: 'https://apexbaank.com/rewards',
    category: 'typosquatting',
    severity: 'high',
    status: 'under_investigation',
    source: 'dns_monitor',
    riskScore: 84,
    modelConfidence: 89,
    scoringVersion: 'RiskGuard-v4.2.1-hybrid',
    riskExplanation: 'Typosquatting permutation with double-vowel insertion ("baank"). Redirects to fraudulent cashback lottery collecting credit card details.',
    domainSimilarityScore: 93,
    visualSimilarityScore: 78,
    logoSimilarityScore: 85,
    scamLanguageDetected: true,
    firstSeenAt: '2026-10-08T11:20:00Z',
    lastObservedAt: '2026-10-09T14:10:00Z',
    ipAddress: '194.38.21.90',
    hostingProvider: 'DigitalOcean Netherlands LLC',
    registrar: 'Tucows Inc.',
    targetGeo: 'US, UK, CA',
    reportedByCount: 8,
    campaignId: 'camp_01',
    analystNotes: [
      'Domain parked until 24 hours ago, when reverse proxy started forwarding to malicious survey funnel.',
      'Analyst marked for prioritized UDRP / abuse takedown.'
    ],
    takedownStatus: {
      requestedAt: '2026-10-09T12:00:00Z',
      authorityContacted: 'Tucows Abuse & Registrar Operations',
      ticketId: 'TUCOWS-48190',
      status: 'acknowledged',
      estimatedResolution: '12-24 hours'
    },
    evidence: [
      {
        id: 'ev_4',
        type: 'dom_diff',
        title: 'Form Redirection to External C2 Server',
        description: 'Form submission endpoint points directly to rogue telemetry host `https://gate-collector.xyz/api/cc-dump`.',
        confidenceScore: 92,
        capturedAt: '2026-10-08T11:25:00Z',
        data: {
          formAction: 'https://gate-collector.xyz/api/cc-dump',
          fieldsCaptured: ['card_number', 'exp_date', 'cvv', 'cardholder_ssn']
        }
      }
    ]
  },
  {
    id: 'threat_apex_03',
    brandId: 'brand_apex_bank',
    targetDomainOrUrl: 'https://twitter.com/ApexBankSupport_Help',
    category: 'social_impersonation',
    severity: 'high',
    status: 'takedown_requested',
    source: 'customer_report',
    riskScore: 88,
    modelConfidence: 92,
    scoringVersion: 'RiskGuard-v4.2.1-hybrid',
    riskExplanation: 'Fake customer support handle directly messaging frustrated bank customers with phishing links requesting seed phrases and 2FA credentials.',
    domainSimilarityScore: 75,
    visualSimilarityScore: 96,
    logoSimilarityScore: 95,
    scamLanguageDetected: true,
    firstSeenAt: '2026-10-07T16:45:00Z',
    lastObservedAt: '2026-10-09T17:00:00Z',
    reportedByCount: 23,
    analystNotes: [
      'X/Twitter Trust & Safety ticket escalated via BrandShield VIP fast-track partner queue.',
      'Account has replied to 34 legitimate customer tweets in past 48 hours.'
    ],
    takedownStatus: {
      requestedAt: '2026-10-08T09:30:00Z',
      authorityContacted: 'X Brand Protection Desk',
      ticketId: 'X-BP-789012',
      status: 'pending',
      estimatedResolution: '2-4 hours'
    },
    evidence: [
      {
        id: 'ev_5',
        type: 'screenshot',
        title: 'DM Screenshot Evidence from Victim',
        description: 'Customer shared DM screenshot showing impersonator offering "Emergency Wallet Unlock" for a $50 transaction fee.',
        confidenceScore: 96,
        capturedAt: '2026-10-08T09:10:00Z',
        data: {
          handle: '@ApexBankSupport_Help',
          creationDate: 'October 2026',
          followersCount: 12
        }
      }
    ]
  },
  {
    id: 'threat_apex_04',
    brandId: 'brand_apex_bank',
    targetDomainOrUrl: 'ApexBank Mobile Assistant (Rogue APK v2.1.0)',
    category: 'mobile_malware',
    severity: 'critical',
    status: 'under_investigation',
    source: 'threat_intelligence_feed',
    riskScore: 99,
    modelConfidence: 97,
    scoringVersion: 'RiskGuard-v4.2.1-hybrid',
    riskExplanation: 'Trojanized Android package distributing banking overlay malware that intercepts SMS OTP codes and keylogs banking credentials.',
    domainSimilarityScore: 90,
    visualSimilarityScore: 92,
    logoSimilarityScore: 96,
    scamLanguageDetected: true,
    firstSeenAt: '2026-10-06T20:00:00Z',
    lastObservedAt: '2026-10-09T10:00:00Z',
    reportedByCount: 5,
    campaignId: 'camp_01',
    analystNotes: [
      'APK hosted on third-party Russian forum `apk-download-vault.ru`.',
      'Package SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.',
      'Google Play Protect team alerted with malware telemetry signature.'
    ],
    evidence: [
      {
        id: 'ev_6',
        type: 'dom_diff',
        title: 'Accessibility Overlay Injection Code',
        description: 'Disassembled DEX bytecode contains permission requests for BIND_ACCESSIBILITY_SERVICE and RECEIVE_SMS.',
        confidenceScore: 99,
        capturedAt: '2026-10-06T20:30:00Z',
        data: {
          malwareFamily: 'Godfather / Anatsa banking Trojan variant',
          permissionsRequested: ['BIND_ACCESSIBILITY_SERVICE', 'RECEIVE_SMS', 'SYSTEM_ALERT_WINDOW']
        }
      }
    ]
  },
  {
    id: 'threat_apex_05',
    brandId: 'brand_apex_bank',
    targetDomainOrUrl: 'https://apex-banking-portal-update.org',
    category: 'credential_harvesting',
    severity: 'medium',
    status: 'resolved',
    source: 'automated_crawler',
    riskScore: 62,
    modelConfidence: 82,
    scoringVersion: 'RiskGuard-v4.2.1-hybrid',
    riskExplanation: 'Dormant phishing template hosted on compromised WordPress site. Cleaned and taken offline following webmaster contact.',
    domainSimilarityScore: 78,
    visualSimilarityScore: 65,
    logoSimilarityScore: 70,
    scamLanguageDetected: false,
    firstSeenAt: '2026-10-01T08:00:00Z',
    lastObservedAt: '2026-10-03T14:00:00Z',
    reportedByCount: 2,
    analystNotes: [
      'Webmaster notified. Malicious sub-directory deleted.',
      'Domain returned HTTP 404 response on all re-verification crawls.'
    ],
    evidence: []
  },
  {
    id: 'threat_apex_06',
    brandId: 'brand_apex_bank',
    targetDomainOrUrl: 'https://apex-community-forum.tech',
    category: 'phishing_website',
    severity: 'low',
    status: 'false_positive',
    source: 'automated_crawler',
    riskScore: 28,
    modelConfidence: 88,
    scoringVersion: 'RiskGuard-v4.2.1-hybrid',
    riskExplanation: 'Legitimate independent developer community discussing Apex open APIs. No deceptive logos, phishing forms, or malicious scripts detected.',
    domainSimilarityScore: 54,
    visualSimilarityScore: 12,
    logoSimilarityScore: 8,
    scamLanguageDetected: false,
    firstSeenAt: '2026-09-28T10:00:00Z',
    lastObservedAt: '2026-10-08T09:00:00Z',
    reportedByCount: 0,
    analystNotes: [
      'Reviewed by Security Analyst Marcus Vance. Verified as non-infringing community resource. Allowlisted in crawler engine.'
    ],
    evidence: []
  }
];

export const MOCK_REPORTS: CustomerReport[] = [
  {
    id: 'rep_1001',
    reporterUserId: 'user_cust_1',
    reporterPhone: '+1 (555) 902-1144',
    brandId: 'brand_apex_bank',
    brandName: 'ApexBank Global',
    category: 'phishing_website',
    targetUrlOrIdentifier: 'https://apex-bank-secure-login.net/verify',
    description: 'I received an SMS claiming my debit card was suspended and asking me to log in urgently on this link. When I opened the page, it looked almost identical to ApexBank, but the URL looked suspicious.',
    evidenceFiles: [
      {
        id: 'file_1',
        filename: 'sms_screenshot_fraud.png',
        url: 'https://images.unsplash.com/photo-1563986768609-322da13575f3?w=300&auto=format&fit=crop&q=80',
        fileType: 'image/png',
        uploadedAt: '2026-10-09T05:30:00Z'
      }
    ],
    scamTactics: ['Urgent SMS alert', 'Fake login screen', '2FA code theft prompt'],
    status: 'under_investigation',
    submittedAt: '2026-10-09T05:35:00Z',
    updatedAt: '2026-10-09T08:15:00Z',
    resolutionNotes: 'Report validated by ApexBank Security Operations. Domain added to global blocklist and active takedown request submitted to registrar.'
  },
  {
    id: 'rep_1002',
    reporterUserId: 'user_cust_2',
    reporterPhone: '+1 (555) 774-8821',
    brandId: 'brand_apex_bank',
    brandName: 'ApexBank Global',
    category: 'fake_social_profile',
    targetUrlOrIdentifier: 'https://twitter.com/ApexBankSupport_Help',
    description: 'This Twitter account reached out via direct message after I tweeted about a transfer delay. They asked for my phone number and one-time password.',
    evidenceFiles: [],
    scamTactics: ['Social media impersonation', 'Direct message phishing', 'Requesting OTP'],
    status: 'takedown_initiated',
    submittedAt: '2026-10-08T09:12:00Z',
    updatedAt: '2026-10-08T10:45:00Z',
    resolutionNotes: 'X Brand Protection desk contacted. Escalated as high severity impersonation.'
  },
  {
    id: 'rep_1003',
    reporterUserId: 'user_cust_1',
    reporterPhone: '+1 (555) 902-1144',
    brandId: 'brand_aurapay',
    brandName: 'AuraPay Checkout',
    category: 'scam_sms_whatsapp',
    targetUrlOrIdentifier: '+1-800-FAKE-PAY / SMS Scam link',
    description: 'Received a WhatsApp message saying I won $500 cashback on AuraPay. Asked to click a link with bit.ly shortener.',
    evidenceFiles: [],
    scamTactics: ['Fake cash prize', 'URL shortener obscuring domain'],
    status: 'resolved',
    submittedAt: '2026-10-04T12:00:00Z',
    updatedAt: '2026-10-05T16:00:00Z',
    resolutionNotes: 'Shortener link deactivated by Bitly Trust & Safety. Target hosting suspended.'
  }
];

export const MOCK_REVIEWS: CustomerReview[] = [
  {
    id: 'rev_1',
    brandId: 'brand_apex_bank',
    brandName: 'ApexBank Global',
    userId: 'user_cust_1',
    userName: 'David C.',
    userPhoneMasked: '+1 (555) ***-1144',
    isPhoneVerified: true,
    rating: 5,
    title: 'Extremely proactive threat response & great communication',
    comment: 'I reported a spoofed SMS link targeting my account this morning. Within 2 hours, BrandShield & ApexBank notified me that the site was flagged and blocked. Outstanding customer protection.',
    createdAt: '2026-10-09T09:30:00Z',
    upvotesCount: 42,
    isCustomerVerifiedOnly: true,
    verifiedProof: {
      type: 'invoice_receipt',
      referenceId: 'INV-2026-APEX-98124',
      proofFileName: 'ApexBank_Commercial_Account_Receipt_Oct2026.pdf',
      proofFileUrl: 'https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=600&auto=format&fit=crop&q=80',
      verificationTimestamp: '2026-10-09T09:25:00Z',
      verificationStatus: 'verified_authentic',
      proofScore: 99,
      orderAmount: '$2,450.00 / mo',
      productOrServicePurchased: 'Apex Global Premier Commercial Treasury & Fraud Shield',
      cryptographicHash: '0x8f2b4c1098e722a1b92015df33aa110992a831e508821a4f00bc19283748291a'
    },
    brandResponse: {
      responderName: 'ApexBank Security Team',
      responderRole: 'Director of Fraud Intelligence',
      response: 'Thank you David! Your early report helped us neutralize this phishing domain before other customers were impacted. Your vigilance makes our ecosystem safer for everyone.',
      respondedAt: '2026-10-09T10:15:00Z'
    }
  },
  {
    id: 'rev_2',
    brandId: 'brand_apex_bank',
    brandName: 'ApexBank Global',
    userId: 'user_cust_2',
    userName: 'Sarah J.',
    userPhoneMasked: '+1 (555) ***-8821',
    isPhoneVerified: true,
    rating: 5,
    title: 'Verified official handles saved me from a Twitter scam',
    comment: 'Having the verified official social handles clearly listed here helped me immediately realize the fake support bot in my DMs was a fraudster. Love the transparency.',
    createdAt: '2026-10-08T14:10:00Z',
    upvotesCount: 29,
    isCustomerVerifiedOnly: true,
    verifiedProof: {
      type: 'transaction_ref',
      referenceId: 'TXN-APX-8829104921',
      proofFileName: 'Wire_Transfer_Verification_Confirmation_Signed.jpg',
      proofFileUrl: 'https://images.unsplash.com/photo-1563986768609-322da13575f3?w=600&auto=format&fit=crop&q=80',
      verificationTimestamp: '2026-10-08T14:05:00Z',
      verificationStatus: 'verified_authentic',
      proofScore: 98,
      orderAmount: '$15,800.00',
      productOrServicePurchased: 'Apex International Wire Gateway & Multi-Currency Account',
      cryptographicHash: '0x3c719e8a5b2100492a8e771c99104fae1098055419992018ea194729019284fa'
    },
    brandResponse: {
      responderName: 'Elena Rostova',
      responderRole: 'Brand Protection Lead',
      response: 'We are delighted to hear that Sarah! Always make sure to refer only to our verified badges listed on BrandShield AI.',
      respondedAt: '2026-10-08T15:00:00Z'
    }
  },
  {
    id: 'rev_4',
    brandId: 'brand_apex_bank',
    brandName: 'ApexBank Global',
    userId: 'user_cust_4',
    userName: 'Michael Zhang',
    userPhoneMasked: '+1 (555) ***-3329',
    isPhoneVerified: true,
    rating: 4,
    title: 'Instant dispute resolution on flagged scam transaction',
    comment: 'When I received a phishing SMS and accidentally clicked it, ApexBank automated lock intervened instantly. I was able to verify my identity via OTP and unlocked my corporate card in minutes.',
    createdAt: '2026-10-07T11:45:00Z',
    upvotesCount: 15,
    isCustomerVerifiedOnly: true,
    verifiedProof: {
      type: 'phone_otp_and_contract',
      referenceId: 'AUTH-OTP-7719283-CORP',
      proofFileName: 'Digital_Signature_Verification_Doc_Apex.pdf',
      proofFileUrl: 'https://images.unsplash.com/photo-1450133064473-71024230f91b?w=600&auto=format&fit=crop&q=80',
      verificationTimestamp: '2026-10-07T11:40:00Z',
      verificationStatus: 'verified_authentic',
      proofScore: 96,
      orderAmount: '$8,200.00 / yr',
      productOrServicePurchased: 'Corporate Executive Platinum Card & Fraud Guard',
      cryptographicHash: '0x12a99d45e09f87123ca4901bce55490192837499102837492910485729103984'
    }
  },
  {
    id: 'rev_3',
    brandId: 'brand_lumina',
    brandName: 'Lumina Cloud',
    userId: 'user_cust_3',
    userName: 'Alex R.',
    userPhoneMasked: '+1 (555) ***-4099',
    isPhoneVerified: true,
    rating: 5,
    title: 'Flawless developer security & fast API verification',
    comment: 'Lumina\'s domain verification and webhook signatures are rock solid. Never had a single impersonation issue since they onboarded.',
    createdAt: '2026-10-05T17:20:00Z',
    upvotesCount: 18,
    isCustomerVerifiedOnly: true,
    verifiedProof: {
      type: 'crypto_tx_or_order',
      referenceId: 'ORD-LUM-2026-00481',
      proofFileName: 'Lumina_Enterprise_Cloud_Subscription_Invoice.pdf',
      proofFileUrl: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&auto=format&fit=crop&q=80',
      verificationTimestamp: '2026-10-05T17:15:00Z',
      verificationStatus: 'verified_authentic',
      proofScore: 100,
      orderAmount: '$3,800.00 / mo',
      productOrServicePurchased: 'Lumina Cloud Enterprise Cluster & WAF Node Suite',
      cryptographicHash: '0x55d88f912ca87410029b41a99f0129a009848123910924901928374920194821'
    }
  }
];

export const MOCK_CAMPAIGNS: ThreatCampaign[] = [
  {
    id: 'camp_01',
    brandId: 'brand_apex_bank',
    name: 'Operation "PhishVault 2026" Credential Syndicate',
    threatActor: 'Fin7 / SilentShadow Threat Cluster',
    detectedAt: '2026-10-06T18:00:00Z',
    severity: 'critical',
    status: 'active',
    summary: 'Coordinated multi-vector campaign deploying typosquatted domains, rogue Android malware APKs, and bulk automated SMS lures aimed at harvesting banking 2FA passcodes.',
    associatedThreatIds: ['threat_apex_01', 'threat_apex_02', 'threat_apex_04'],
    affectedCustomerCountEst: 1400,
    targetedRegions: ['United States', 'Canada', 'United Kingdom'],
    primaryAttackVectors: ['Smishing (SMS Lures)', 'Domain Typosquatting', 'Trojanized APK Overlay']
  },
  {
    id: 'camp_02',
    brandId: 'brand_apex_bank',
    name: 'Support Bot Impersonation Swarm',
    threatActor: 'Automated Botnet Farm #19',
    detectedAt: '2026-09-20T12:00:00Z',
    severity: 'medium',
    status: 'contained',
    summary: 'Scraper bots monitoring Twitter brand mentions to inject rogue customer support URLs within 45 seconds of tweet publication.',
    associatedThreatIds: ['threat_apex_03'],
    affectedCustomerCountEst: 350,
    targetedRegions: ['Global English Speakers'],
    primaryAttackVectors: ['X / Twitter Scraping', 'Direct Message Phishing']
  },
  {
    id: 'camp_03',
    brandId: 'brand_apex_bank',
    name: 'Executive Wire-Fraud Syndicate',
    threatActor: 'Cobalt Mirage Group',
    detectedAt: '2026-10-02T14:30:00Z',
    severity: 'high',
    status: 'active',
    summary: 'Targeted LinkedIn executive impersonation and fake corporate emails designed to intercept customer funds and wire authorizations.',
    associatedThreatIds: ['threat_apex_01', 'threat_apex_03'],
    affectedCustomerCountEst: 420,
    targetedRegions: ['United States', 'Singapore', 'European Union'],
    primaryAttackVectors: ['Executive Social Profiling', 'Lookalike Mail Spoofing', 'Wire Redirection']
  }
];

export const MOCK_ALERTS: SecurityAlert[] = [
  {
    id: 'alert_1',
    brandId: 'brand_apex_bank',
    title: 'Critical Phishing Domain Detected',
    message: 'New high-risk clone `apex-bank-secure-login.net` detected with 96% AI risk score.',
    severity: 'critical',
    category: 'phishing_website',
    threatId: 'threat_apex_01',
    timestamp: '15 minutes ago',
    isRead: false,
    actionUrl: '/brand-owner/threats/threat_apex_01'
  },
  {
    id: 'alert_2',
    brandId: 'brand_apex_bank',
    title: 'Customer Takedown Escalation',
    message: 'Report #REP-1002 reached 20+ verified community confirmations on social impersonator.',
    severity: 'high',
    category: 'social_impersonation',
    threatId: 'threat_apex_03',
    timestamp: '2 hours ago',
    isRead: false,
    actionUrl: '/brand-owner/threats/threat_apex_03'
  },
  {
    id: 'alert_3',
    brandId: 'brand_apex_bank',
    title: 'DNS Permutation Scanner Alert',
    message: '3 new typosquatted domain variations registered across international registrars.',
    severity: 'medium',
    category: 'typosquatting',
    timestamp: '5 hours ago',
    isRead: true,
    actionUrl: '/brand-owner/suspicious-websites'
  }
];
