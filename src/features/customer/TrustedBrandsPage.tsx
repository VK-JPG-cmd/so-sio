import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBrand } from '../../context/BrandContext';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { SearchInput } from '../../components/ui/Input';
import { 
  ShieldCheck, 
  ExternalLink, 
  Star, 
  Globe2, 
  Share2, 
  Smartphone,
  Shield,
  Search,
  Filter
} from 'lucide-react';

export const TrustedBrandsPage: React.FC = () => {
  const { brands } = useBrand();
  const [search, setSearch] = useState('');
  const [selectedIndustry, setSelectedIndustry] = useState('All');
  const navigate = useNavigate();

  const industries = ['All', 'Banking & Fintech', 'E-commerce & Retail', 'SaaS & Enterprise'];

  const filteredBrands = brands.filter((b) => {
    const matchesSearch = 
      b.name.toLowerCase().includes(search.toLowerCase()) ||
      b.officialWebsite.toLowerCase().includes(search.toLowerCase()) ||
      b.description.toLowerCase().includes(search.toLowerCase());

    const matchesIndustry = selectedIndustry === 'All' || b.industry === selectedIndustry;
    return matchesSearch && matchesIndustry;
  });

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Title */}
      <div>
        <h1 className="text-2xl font-extrabold text-brand-dark tracking-tight">Verified Trusted Brands</h1>
        <p className="text-xs text-brand-muted mt-1">
          Explore organizations with cryptographically verified domains and active anti-impersonation protection.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <Card padding="sm">
        <div className="flex flex-col md:flex-row items-center gap-3">
          <div className="w-full md:flex-1">
            <SearchInput
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by brand name, official website, or industry..."
            />
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
            {industries.map((ind) => (
              <button
                key={ind}
                onClick={() => setSelectedIndustry(ind)}
                className={`px-3 py-2 rounded-xl text-xs font-bold shrink-0 transition-all ${
                  selectedIndustry === ind
                    ? 'bg-[#111312] text-[#FBF5A5] border border-[#111312] shadow-sm font-bold'
                    : 'text-brand-muted hover:text-brand-dark hover:bg-brand-surface-light'
                }`}
              >
                {ind}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Brand Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredBrands.map((brand) => (
          <Card
            key={brand.id}
            hoverEffect
            onClick={() => navigate(`/customer/brands/${brand.slug}`)}
            className="flex flex-col justify-between space-y-4"
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <img
                    src={brand.logoUrl}
                    alt={brand.name}
                    className="w-14 h-14 rounded-2xl object-cover border border-brand-border shadow-sm"
                  />
                  <div>
                    <h3 className="text-base font-bold text-brand-dark">{brand.name}</h3>
                    <span className="text-xs text-brand-muted">{brand.industry}</span>
                  </div>
                </div>

                <Badge variant="status" status={brand.verificationStatus} size="sm" />
              </div>

              <p className="text-xs text-brand-muted line-clamp-2 leading-relaxed">
                {brand.description}
              </p>

              {/* Assets Preview List */}
              <div className="p-3 rounded-2xl bg-brand-surface-light border border-brand-border space-y-1 text-xs">
                <span className="text-[10px] font-bold text-brand-muted uppercase tracking-wider">Verified Channels</span>
                <div className="flex items-center gap-3 text-brand-dark font-medium pt-1">
                  <span className="flex items-center gap-1">
                    <Globe2 className="w-3.5 h-3.5 text-[#111312]" /> {brand.officialWebsite.replace(/^https?:\/\//, '')}
                  </span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-brand-border/60 flex items-center justify-between text-xs">
              <div className="flex items-center gap-1 text-amber-500 font-bold">
                <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                <span>{brand.customerRating}</span>
                <span className="text-[10px] text-brand-muted font-normal">({brand.reviewsCount} reviews)</span>
              </div>

              <span className="font-extrabold text-emerald-600 flex items-center gap-1">
                <ShieldCheck className="w-4 h-4" />
                {brand.trustScore}% Trust
              </span>
            </div>
          </Card>
        ))}
      </div>

    </div>
  );
};
