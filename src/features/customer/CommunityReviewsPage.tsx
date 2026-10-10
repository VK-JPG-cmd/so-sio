import React, { useState, useEffect } from 'react';
import { useBrand } from '../../context/BrandContext';
import { reviewService } from '../../services/api';
import { CustomerReview } from '../../types';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { useNotification } from '../../context/NotificationContext';
import { VerifiedReviewModal } from '../../components/customer/VerifiedReviewModal';
import { 
  Star, 
  MessageSquareHeart, 
  ShieldCheck, 
  ThumbsUp, 
  CheckCircle2, 
  Filter,
  Search,
  Receipt,
  FileText,
  DollarSign,
  Lock,
  UserCheck,
  PlusCircle,
  ExternalLink
} from 'lucide-react';

export const CommunityReviewsPage: React.FC = () => {
  const { brands } = useBrand();
  const { showToast } = useNotification();
  const [reviews, setReviews] = useState<CustomerReview[]>([]);
  const [selectedBrand, setSelectedBrand] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);

  useEffect(() => {
    const load = async () => {
      const data = await reviewService.getReviews();
      setReviews(data);
    };
    load();
  }, []);

  const handleUpvote = async (reviewId: string) => {
    try {
      const updated = await reviewService.upvoteReview(reviewId);
      setReviews(reviews.map(r => r.id === reviewId ? updated : r));
      showToast({ type: 'success', title: 'Upvoted', message: 'Thanks for supporting authentic feedback.' });
    } catch (err) {
      // ignore
    }
  };

  const handleNewReviewSubmitted = (newRev: CustomerReview) => {
    setReviews([newRev, ...reviews]);
  };

  const filtered = reviews.filter((r) => {
    const matchesBrand = selectedBrand === 'all' || r.brandId === selectedBrand;
    const matchesSearch = 
      r.title.toLowerCase().includes(search.toLowerCase()) ||
      r.comment.toLowerCase().includes(search.toLowerCase()) ||
      r.brandName.toLowerCase().includes(search.toLowerCase()) ||
      (r.verifiedProof?.productOrServicePurchased || '').toLowerCase().includes(search.toLowerCase()) ||
      (r.verifiedProof?.referenceId || '').toLowerCase().includes(search.toLowerCase());
    return matchesBrand && matchesSearch;
  });

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Title & Upload Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-[#111312] bg-[#F4F3EF] px-2.5 py-0.5 rounded-full border border-[#DCDAD4]">
              Verified Customer Trust Feed
            </span>
            <span className="text-xs font-bold text-emerald-700 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> 100% Cryptographic Proof Backed
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-brand-dark tracking-tight mt-1">
            Community Trust & Security Reviews
          </h1>
          <p className="text-xs sm:text-sm text-brand-muted mt-1 max-w-2xl">
            Read authentic feedback from phone-verified consumers with purchase proofs, and review verified brand owner responses.
          </p>
        </div>

        <Button
          variant="primary"
          onClick={() => setIsReviewModalOpen(true)}
          leftIcon={<PlusCircle className="w-4 h-4" />}
          className="shrink-0"
        >
          Upload Verified Review with Proof
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <Card padding="sm">
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-brand-muted absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search reviews by brand, product, order ID, or topic..."
              className="w-full rounded-2xl bg-brand-surface-light border border-brand-border pl-10 pr-4 py-2 text-xs text-brand-dark focus:bg-white focus:outline-none focus:border-[#111312]"
            />
          </div>

          <select
            value={selectedBrand}
            onChange={(e) => setSelectedBrand(e.target.value)}
            className="w-full sm:w-auto rounded-2xl bg-brand-surface-light border border-brand-border px-3 py-2 text-xs font-bold text-brand-dark focus:outline-none focus:border-[#111312]"
          >
            <option value="all">All Verified Brands ({brands.length})</option>
            {brands.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        </div>
      </Card>

      {/* Reviews Feed */}
      <div className="space-y-4">
        {filtered.map((rev) => (
          <Card key={rev.id} className="space-y-4 border border-brand-border/90 hover:border-[#111312]/40 transition-all">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-2xl bg-[#111312] text-[#FBF5A5] flex items-center justify-center font-bold text-sm shrink-0 shadow-soft">
                  {rev.userName.slice(0, 1)}
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h4 className="text-xs font-bold text-brand-dark">{rev.userName}</h4>
                    <span className="text-xs font-bold text-[#111312] px-2 py-0.5 rounded-full bg-[#F4F3EF] border border-[#DCDAD4]">
                      {rev.brandName}
                    </span>
                    {rev.isPhoneVerified && (
                      <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 font-semibold flex items-center gap-1">
                        <CheckCircle2 className="w-2.5 h-2.5" /> Phone OTP Verified
                      </span>
                    )}
                    <span className="text-[10px] text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full border border-teal-200 font-semibold flex items-center gap-1">
                      <ShieldCheck className="w-2.5 h-2.5" /> Customer Proof Validated
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-amber-400 mt-0.5">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className={`w-3.5 h-3.5 ${i < rev.rating ? 'fill-amber-400' : 'text-gray-300'}`} />
                    ))}
                    <span className="text-[11px] font-bold text-brand-dark ml-1">{rev.rating}.0</span>
                    <span className="text-[10px] text-brand-muted">•</span>
                    <span className="text-[10px] text-brand-muted">
                      {new Date(rev.createdAt).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}
                    </span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => handleUpvote(rev.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#F8F7F4] hover:bg-[#F4F3EF] border border-brand-border text-xs text-brand-muted hover:text-[#111312] transition-colors font-semibold shrink-0"
              >
                <ThumbsUp className="w-3.5 h-3.5" />
                <span>{rev.upvotesCount}</span>
              </button>
            </div>

            {/* Product Tag & Reference */}
            {rev.verifiedProof?.productOrServicePurchased && (
              <div className="flex items-center gap-2 text-xs flex-wrap">
                <span className="text-brand-muted">Verified Product:</span>
                <span className="font-bold text-brand-dark px-2 py-0.5 rounded-md bg-[#F4F3EF] border border-brand-border">
                  {rev.verifiedProof.productOrServicePurchased}
                </span>
                {rev.verifiedProof.orderAmount && (
                  <span className="text-emerald-700 font-bold text-[11px] px-2 py-0.5 rounded-md bg-emerald-50 border border-emerald-200">
                    {rev.verifiedProof.orderAmount}
                  </span>
                )}
                {rev.verifiedProof.referenceId && (
                  <span className="font-mono text-[10px] text-brand-muted bg-[#F8F7F4] px-2 py-0.5 rounded-md border border-brand-border">
                    Ref: {rev.verifiedProof.referenceId}
                  </span>
                )}
              </div>
            )}

            <div>
              <h5 className="text-sm font-bold text-brand-dark">{rev.title}</h5>
              <p className="text-xs text-brand-muted mt-1 leading-relaxed">{rev.comment}</p>
            </div>

            {/* Proof Attachment Card */}
            {rev.verifiedProof && (
              <div className="p-3 rounded-2xl bg-[#F8F7F4] border border-brand-border flex items-center justify-between gap-3 text-xs">
                <div className="flex items-center gap-2">
                  <Receipt className="w-4 h-4 text-[#111312] shrink-0" />
                  <span className="text-brand-dark font-medium truncate">
                    Attached Proof: <strong className="font-mono">{rev.verifiedProof.proofFileName}</strong>
                  </span>
                </div>
                <span className="text-emerald-700 font-bold text-[11px] shrink-0 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                  ✓ {rev.verifiedProof.proofScore}% Validated Score
                </span>
              </div>
            )}

            {/* Official Brand Response */}
            {rev.brandResponse && (
              <div className="p-4 rounded-2xl bg-[#F8F7F4] border border-[#E2E1DC] text-xs border-l-4 border-l-[#111312] space-y-1.5 ml-2 sm:ml-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <div className="flex items-center gap-1.5 font-bold text-[#111312]">
                    <ShieldCheck className="w-4 h-4 text-[#111312] shrink-0" />
                    <span>Official Response from {rev.brandResponse.responderName}</span>
                    <span className="text-[10px] text-brand-muted font-normal">({rev.brandResponse.responderRole})</span>
                  </div>
                  <span className="text-[10px] text-brand-muted">
                    {new Date(rev.brandResponse.respondedAt).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-xs text-brand-dark leading-relaxed">
                  {rev.brandResponse.response}
                </p>
              </div>
            )}
          </Card>
        ))}
      </div>

      {/* Verified Review Upload Modal */}
      <VerifiedReviewModal
        isOpen={isReviewModalOpen}
        onClose={() => setIsReviewModalOpen(false)}
        onReviewSubmitted={handleNewReviewSubmitted}
        defaultBrandId={selectedBrand !== 'all' ? selectedBrand : undefined}
      />

    </div>
  );
};
