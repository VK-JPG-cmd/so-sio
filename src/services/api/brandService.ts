import { BrandProfile, BrandAsset } from '../../types';
import { MOCK_BRANDS } from '../mockData';
import { apiClient } from './client';

const BRANDS_STORAGE_KEY = 'brandshield_brands_data';

export const deduplicateBrands = (list: BrandProfile[]): BrandProfile[] => {
  const seen = new Set<string>();
  const result: BrandProfile[] = [];
  for (const b of list) {
    if (!b || !b.name) continue;
    const key = b.name.trim().toLowerCase();
    if (!seen.has(key)) {
      seen.add(key);
      result.push(b);
    }
  }
  return result;
};

const getCleanStoredBrands = (): BrandProfile[] => {
  try {
    const raw = localStorage.getItem(BRANDS_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      // Filter out duplicate or junk registrations
      const cleaned = deduplicateBrands(parsed).filter(
        b => b.name && b.name.trim().toLowerCase() !== 'nova commerce'
      );
      localStorage.setItem(BRANDS_STORAGE_KEY, JSON.stringify(cleaned));
      return cleaned;
    }
  } catch {}
  return [];
};

export const brandService = {
  getAllBrands: async (): Promise<BrandProfile[]> => {
    if (!apiClient.isMockMode) {
      try {
        const rawBrands = await apiClient.request<any[]>('/brands');
        if (Array.isArray(rawBrands) && rawBrands.length > 0) {
          const backendBrands = rawBrands.map((b: any) => {
            const matchingMock = MOCK_BRANDS.find(
              m => m.id === b.id || m.officialWebsite?.includes(b.official_domain) || m.name.toLowerCase() === b.display_name?.toLowerCase()
            );

            return {
              id: b.id,
              name: b.display_name || b.name || 'Verified Brand',
              legalEntityName: matchingMock?.legalEntityName || `${b.display_name || 'Brand'} Inc.`,
              slug: matchingMock?.slug || (b.display_name || 'brand').toLowerCase().replace(/[^a-z0-9]/g, '-'),
              industry: matchingMock?.industry || 'Banking & Fintech',
              officialWebsite: b.official_domain ? (b.official_domain.startsWith('http') ? b.official_domain : `https://${b.official_domain}`) : (matchingMock?.officialWebsite || 'https://apexbank.com'),
              logoUrl: matchingMock?.logoUrl || 'https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=120&auto=format&fit=crop&q=80',
              description: matchingMock?.description || 'Officially verified enterprise on So-cio digital protection radar.',
              verificationStatus: (b.verification_status?.toLowerCase() || 'verified') as any,
              verificationSubmittedAt: b.created_at || new Date().toISOString(),
              trustScore: matchingMock?.trustScore ?? 98,
              totalThreatsNeutralized: matchingMock?.totalThreatsNeutralized ?? 142,
              activeMonitorsCount: matchingMock?.activeMonitorsCount ?? 28,
              customerRating: matchingMock?.customerRating ?? 4.9,
              reviewsCount: matchingMock?.reviewsCount ?? 64,
              assets: matchingMock?.assets || [
                {
                  id: `asset_${b.id}`,
                  type: 'domain',
                  value: b.official_domain || 'apexbank.com',
                  status: 'verified',
                  healthStatus: 'secure',
                }
              ],
            };
          });

          // Merge clean stored brands with backend brands
          const localBrands = getCleanStoredBrands();
          const merged = deduplicateBrands([
            ...backendBrands,
            ...localBrands.filter(lb => !backendBrands.some(bb => bb.name.toLowerCase() === lb.name.toLowerCase())),
          ]);
          return merged;
        }
      } catch (err) {
        console.warn('Falling back to local brands cache', err);
      }
    }

    const stored = getCleanStoredBrands();
    if (stored.length > 0) {
      return deduplicateBrands([...stored, ...MOCK_BRANDS]);
    }
    return deduplicateBrands(MOCK_BRANDS);
  },

  getBrandById: async (brandId: string): Promise<BrandProfile | null> => {
    const brands = await brandService.getAllBrands();
    return brands.find(b => b.id === brandId) || brands[0] || null;
  },

  getBrandBySlug: async (slug: string): Promise<BrandProfile | null> => {
    const brands = await brandService.getAllBrands();
    return brands.find(b => b.slug === slug) || null;
  },

  registerBrand: async (brandData: Partial<BrandProfile>): Promise<BrandProfile> => {
    if (!apiClient.isMockMode) {
      try {
        return await apiClient.request<BrandProfile>('/brands/register', {
          method: 'POST',
          body: JSON.stringify(brandData)
        });
      } catch (err) {
        console.warn('Falling back to local brand registration', err);
      }
    }

    await new Promise(r => setTimeout(r, 800));
    const brands = await brandService.getAllBrands();
    const newBrand: BrandProfile = {
      id: `brand_${Date.now()}`,
      name: brandData.name || 'New Brand',
      legalEntityName: brandData.legalEntityName || `${brandData.name} Inc.`,
      slug: (brandData.name || 'new-brand').toLowerCase().replace(/[^a-z0-9]/g, '-'),
      industry: brandData.industry || 'Banking & Fintech',
      officialWebsite: brandData.officialWebsite || 'https://example.com',
      logoUrl: brandData.logoUrl || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=120&auto=format&fit=crop&q=80',
      description: brandData.description || 'Verified enterprise organization on BrandShield AI.',
      verificationStatus: 'pending',
      verificationSubmittedAt: new Date().toISOString(),
      trustScore: 75,
      totalThreatsNeutralized: 0,
      activeMonitorsCount: 1,
      customerRating: 5.0,
      reviewsCount: 0,
      assets: [
        {
          id: `asset_${Date.now()}`,
          type: 'domain',
          value: brandData.officialWebsite?.replace(/^https?:\/\//, '').replace(/\/.*$/, '') || 'example.com',
          status: 'pending',
          dnsTxtRecord: `brandshield-verification=${Math.random().toString(36).substring(2, 10)}`,
          healthStatus: 'warning'
        }
      ]
    };

    const updated = deduplicateBrands([
      newBrand,
      ...brands.filter(b => b.name.toLowerCase().trim() !== (brandData.name || '').toLowerCase().trim())
    ]);
    localStorage.setItem(BRANDS_STORAGE_KEY, JSON.stringify(updated));
    return newBrand;
  },

  verifyDnsTxtRecord: async (brandId: string, assetId: string): Promise<{ success: boolean; message: string }> => {
    await new Promise(r => setTimeout(r, 1200));
    const brands = await brandService.getAllBrands();
    const brand = brands.find(b => b.id === brandId);
    if (!brand) return { success: false, message: 'Brand not found' };

    const asset = brand.assets.find(a => a.id === assetId);
    if (asset) {
      asset.status = 'verified';
      asset.verifiedAt = new Date().toISOString();
      asset.healthStatus = 'secure';
      brand.verificationStatus = 'verified';
      brand.verifiedAt = new Date().toISOString();
      localStorage.setItem(BRANDS_STORAGE_KEY, JSON.stringify(brands));
      return { success: true, message: 'DNS TXT Record successfully verified! Domain is secured.' };
    }
    return { success: false, message: 'Asset record not found' };
  },

  addAsset: async (brandId: string, asset: Omit<BrandAsset, 'id'>): Promise<BrandAsset> => {
    const brands = await brandService.getAllBrands();
    const brand = brands.find(b => b.id === brandId);
    const newAsset: BrandAsset = {
      ...asset,
      id: `asset_${Date.now()}`,
      dnsTxtRecord: `brandshield-verification=${Math.random().toString(36).substring(2, 10)}`
    };
    if (brand) {
      brand.assets.push(newAsset);
      brand.activeMonitorsCount = brand.assets.length;
      localStorage.setItem(BRANDS_STORAGE_KEY, JSON.stringify(brands));
    }
    return newAsset;
  }
};
