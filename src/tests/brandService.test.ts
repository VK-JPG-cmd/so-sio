import { describe, it, expect } from 'vitest';
import { brandService } from '../services/api/brandService';
import { threatService } from '../services/api/threatService';
import { reportService } from '../services/api/reportService';

describe('BrandShield Core Security Services', () => {
  it('should fetch verified brands directory', async () => {
    const brands = await brandService.getAllBrands();
    expect(brands.length).toBeGreaterThan(0);
    const apex = brands.find(b => b.slug === 'apex-bank');
    expect(apex).toBeDefined();
    expect(apex?.verificationStatus).toBe('verified');
    expect(apex?.trustScore).toBeGreaterThanOrEqual(90);
  });

  it('should register a new brand with pending verification status', async () => {
    const newBrand = await brandService.registerBrand({
      name: 'CyberPay Inc',
      legalEntityName: 'CyberPay Global Ltd',
      officialWebsite: 'https://cyberpay.io',
      industry: 'Banking & Fintech'
    });

    expect(newBrand.id).toBeDefined();
    expect(newBrand.verificationStatus).toBe('pending');
    expect(newBrand.assets.length).toBeGreaterThan(0);
    expect(newBrand.assets[0].dnsTxtRecord).toContain('brandshield-verification=');
  });

  it('should verify DNS TXT record and promote brand to verified status', async () => {
    const brand = await brandService.registerBrand({
      name: 'Vortex Vault',
      officialWebsite: 'https://vortexvault.io',
    });

    const result = await brandService.verifyDnsTxtRecord(brand.id, brand.assets[0].id);
    expect(result.success).toBe(true);

    const updated = await brandService.getBrandById(brand.id);
    expect(updated?.verificationStatus).toBe('verified');
  }, 10000);

  it('should update threat status and dispatch takedown package', async () => {
    const threats = await threatService.getThreats();
    expect(threats.length).toBeGreaterThan(0);
    
    const targetThreat = threats[0];
    const updated = await threatService.requestTakedown(targetThreat.id, 'Dispatched to NameCheap Abuse');
    
    expect(updated.status).toBe('takedown_requested');
    expect(updated.takedownStatus).toBeDefined();
    expect(updated.takedownStatus?.status).toBe('pending');
  });

  it('should accept customer threat report submissions', async () => {
    const report = await reportService.submitReport({
      brandName: 'ApexBank Global',
      category: 'phishing_website',
      targetUrlOrIdentifier: 'https://apex-fake-verify.xyz',
      description: 'Phishing SMS received claiming urgent KYC update needed.',
      scamTactics: ['Urgent SMS', 'Fake KYC form']
    });

    expect(report.id).toBeDefined();
    expect(report.status).toBe('submitted');
    expect(report.scamTactics).toContain('Urgent SMS');
  });
});
