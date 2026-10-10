import React, { useState, useEffect, useMemo } from 'react';
import { useBrand } from '../../context/BrandContext';
import { reviewService } from '../../services/api';
import { CustomerReview, VerifiedCustomerProof } from '../../types';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { Textarea, Input } from '../../components/ui/Input';
import { useNotification } from '../../context/NotificationContext';
import { 
  Star, 
  MessageSquareHeart, 
  ShieldCheck, 
  ThumbsUp, 
  Reply, 
  CheckCircle2, 
  Sparkles,
  UserCheck,
  FileCheck2,
  Receipt,
  FileText,
  Search,
  Filter,
  ExternalLink,
  Lock,
  Hash,
  Copy,
  Calendar,
  DollarSign,
  AlertCircle,
  Eye,
  Check
} from 'lucide-react';

export const CustomerReviewsPage: React.FC = () => {
  const { currentBrand } = useBrand();
  const { showToast } = useNotification();
  const [reviews, setReviews] = useState<CustomerReview[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [ratingFilter, setRatingFilter] = useState<string>('all');
  const [proofTypeFilter, setProofTypeFilter] = useState<string>('all');
  const [responseFilter, setResponseFilter] = useState<string>('all');

  // Modals
  const [replyModalOpen, setReplyModalOpen] = useState(false);
  const [selectedReview, setSelectedReview] = useState<CustomerReview | null>(null);
  const [responseText, setResponseText] = useState('');
  const [responderRole, setResponderRole] = useState('Brand Protection Lead');
  const [responderName, setResponderName] = useState('Elena Rostova');
  const [isSubmittingReply, setIsSubmittingReply] = useState(false);

  // Proof Inspector Modal
  const [proofModalOpen, setProofModalOpen] = useState(false);
  const [inspectingReview, setInspectingReview] = useState<CustomerReview | null>(null);
  const [copiedHash, setCopiedHash] = useState(false);

  useEffect(() => {
    const loadReviews = async () => {
      setLoading(true);
      if (currentBrand) {
        const data = await reviewService.getReviews(currentBrand.id);
        setReviews(data);
      }
      setLoading(false);
    };
    loadReviews();
  }, [currentBrand]);

  // Filtered reviews
  const filteredReviews = useMemo(() => {
    return reviews.filter(rev => {
      // Search
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch = !q || 
        rev.userName.toLowerCase().includes(q) ||
        rev.title.toLowerCase().includes(q) ||
        rev.comment.toLowerCase().includes(q) ||
        rev.verifiedProof?.referenceId.toLowerCase().includes(q) ||
        rev.verifiedProof?.productOrServicePurchased.toLowerCase().includes(q);

      // Rating
      const matchesRating = ratingFilter === 'all' || rev.rating.toString() === ratingFilter;

      // Proof Type
      const matchesProofType = proofTypeFilter === 'all' || rev.verifiedProof?.type === proofTypeFilter;

      // Response Status
      const matchesResponse = responseFilter === 'all' ||
        (responseFilter === 'replied' && !!rev.brandResponse) ||
        (responseFilter === 'pending' && !rev.brandResponse);

      return matchesSearch && matchesRating && matchesProofType && matchesResponse;
    });
  }, [reviews, searchQuery, ratingFilter, proofTypeFilter, responseFilter]);

  const handleOpenReply = (rev: CustomerReview) => {
    setSelectedReview(rev);
    setResponseText(rev.brandResponse?.response || '');
    setResponderName(rev.brandResponse?.responderName || 'Elena Rostova');
    setResponderRole(rev.brandResponse?.responderRole || 'Brand Protection Lead');
    setReplyModalOpen(true);
  };

  const handleOpenProofInspector = (rev: CustomerReview) => {
    setInspectingReview(rev);
    setCopiedHash(false);
    setProofModalOpen(true);
  };

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(true);
    showToast({ type: 'info', title: 'Hash Copied', message: 'Proof verification hash copied to clipboard.' });
    setTimeout(() => setCopiedHash(false), 2500);
  };

  const handleSendResponse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReview || !responseText.trim()) return;

    setIsSubmittingReply(true);
    try {
      const updated = await reviewService.respondToReview(
        selectedReview.id,
        responseText,
        responderName,
        responderRole
      );
      setReviews(reviews.map(r => r.id === updated.id ? updated : r));
      setReplyModalOpen(false);
      showToast({ 
        type: 'success', 
        title: 'Official Response Published', 
        message: 'Your verified brand response is now visible to customers.' 
      });
    } catch (err) {
      showToast({ type: 'error', title: 'Failed to post reply', message: 'Please check your inputs and try again.' });
    } finally {
      setIsSubmittingReply(false);
    }
  };

  // Metrics calculation
  const totalReviewsCount = reviews.length;
  const avgRating = totalReviewsCount > 0 
    ? (reviews.reduce((acc, r) => acc + r.rating, 0) / totalReviewsCount).toFixed(1) 
    : '5.0';
  const verifiedProofRate = '100%';
  const responseCount = reviews.filter(r => !!r.brandResponse).length;
  const responseRate = totalReviewsCount > 0 ? Math.round((responseCount / totalReviewsCount) * 100) : 100;

  const getProofTypeBadge = (type?: string) => {
    switch (type) {
      case 'invoice_receipt':
        return { label: 'Verified Invoice / Receipt', icon: Receipt, color: 'bg-emerald-50 text-emerald-700 border-emerald-200' };
      case 'transaction_ref':
        return { label: 'Verified Transaction Ref', icon: DollarSign, color: 'bg-blue-50 text-blue-700 border-blue-200' };
      case 'phone_otp_and_contract':
        return { label: 'OTP & Contract Verified', icon: UserCheck, color: 'bg-stone-100 text-[#111312] border-stone-300' };
      case 'crypto_tx_or_order':
        return { label: 'Verified Order ID / Cryptographic Tx', icon: Lock, color: 'bg-teal-50 text-teal-700 border-teal-200' };
      default:
        return { label: 'Verified Customer Proof', icon: ShieldCheck, color: 'bg-emerald-50 text-emerald-700 border-emerald-200' };
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Feature Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#111312] text-[#FBF5A5] border border-[#2B2D2C]">
              Feature 13
            </span>
            <span className="text-xs font-bold text-emerald-700 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> Customer-Only Verified Proofs
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-brand-dark tracking-tight mt-1">
            Customer Reviews & Verified Proof Hub
          </h1>
          <p className="text-xs sm:text-sm text-brand-muted mt-1 max-w-3xl">
            Customer product reviews backed by cryptographic proof, verified order receipts, and Phone OTP validation. Inspect proof artifacts, triage customer feedback, and publish verified brand owner replies.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-[#F4F3EF] border border-[#DCDAD4] flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-bold text-base shadow-soft">
              <Star className="w-5 h-5 fill-white text-white" />
            </div>
            <div>
              <div className="text-base font-extrabold text-brand-dark flex items-center gap-1.5">
                {avgRating} <span className="text-xs text-brand-muted font-normal">/ 5.0</span>
              </div>
              <div className="text-[11px] text-emerald-700 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> 100% Authentic Customer Proof
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Top 4 KPI Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 bg-white/90 border border-brand-border hover:shadow-soft transition-all">
          <div className="flex items-center justify-between text-xs text-brand-muted font-medium mb-1">
            <span>Verified Customer Reviews</span>
            <MessageSquareHeart className="w-4 h-4 text-[#111312]" />
          </div>
          <div className="text-2xl font-extrabold text-brand-dark">{totalReviewsCount}</div>
          <p className="text-[11px] text-brand-muted mt-1">Only Phone OTP + Proof verified customers</p>
        </Card>

        <Card className="p-4 bg-white/90 border border-brand-border hover:shadow-soft transition-all">
          <div className="flex items-center justify-between text-xs text-brand-muted font-medium mb-1">
            <span>Proof Verification Rate</span>
            <FileCheck2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-700">{verifiedProofRate}</div>
          <p className="text-[11px] text-brand-muted mt-1">Zero unverified or bot spam reviews</p>
        </Card>

        <Card className="p-4 bg-white/90 border border-brand-border hover:shadow-soft transition-all">
          <div className="flex items-center justify-between text-xs text-brand-muted font-medium mb-1">
            <span>Brand Owner Response Rate</span>
            <Reply className="w-4 h-4 text-[#111312]" />
          </div>
          <div className="text-2xl font-extrabold text-[#111312]">{responseRate}%</div>
          <p className="text-[11px] text-brand-muted mt-1">{responseCount} of {totalReviewsCount} reviews answered</p>
        </Card>

        <Card className="p-4 bg-white/90 border border-brand-border hover:shadow-soft transition-all">
          <div className="flex items-center justify-between text-xs text-brand-muted font-medium mb-1">
            <span>Customer Trust Score</span>
            <ShieldCheck className="w-4 h-4 text-teal-600" />
          </div>
          <div className="text-2xl font-extrabold text-teal-700">98 / 100</div>
          <p className="text-[11px] text-brand-muted mt-1">High credibility among active customers</p>
        </Card>
      </div>

      {/* Filter and Search Controls */}
      <Card className="p-4 space-y-3 bg-white/90 border border-brand-border">
        <div className="flex flex-col md:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-brand-muted absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by customer name, review keyword, order ref, or product..."
              className="w-full pl-10 pr-4 py-2 text-xs rounded-2xl bg-brand-surface-light border border-brand-border focus:bg-white focus:outline-none focus:border-[#111312] transition-all"
            />
          </div>

          {/* Rating Filter */}
          <select
            value={ratingFilter}
            onChange={(e) => setRatingFilter(e.target.value)}
            className="px-3 py-2 text-xs rounded-2xl bg-brand-surface-light border border-brand-border focus:outline-none focus:border-[#111312] text-brand-dark"
          >
            <option value="all">All Star Ratings</option>
            <option value="5">5 Stars (★★★★★)</option>
            <option value="4">4 Stars (★★★★☆)</option>
            <option value="3">3 Stars (★★★☆☆)</option>
            <option value="2">2 Stars (★★☆☆☆)</option>
            <option value="1">1 Star (★☆☆☆☆)</option>
          </select>

          {/* Proof Type Filter */}
          <select
            value={proofTypeFilter}
            onChange={(e) => setProofTypeFilter(e.target.value)}
            className="px-3 py-2 text-xs rounded-2xl bg-brand-surface-light border border-brand-border focus:outline-none focus:border-[#111312] text-brand-dark"
          >
            <option value="all">All Verified Proof Types</option>
            <option value="invoice_receipt">Invoice / Receipt Upload</option>
            <option value="transaction_ref">Transaction Reference</option>
            <option value="phone_otp_and_contract">Phone OTP & Contract</option>
            <option value="crypto_tx_or_order">Order ID / Cryptographic Tx</option>
          </select>

          {/* Brand Response Filter */}
          <select
            value={responseFilter}
            onChange={(e) => setResponseFilter(e.target.value)}
            className="px-3 py-2 text-xs rounded-2xl bg-brand-surface-light border border-brand-border focus:outline-none focus:border-[#111312] text-brand-dark"
          >
            <option value="all">All Response States</option>
            <option value="replied">Responded by Brand Owner</option>
            <option value="pending">Awaiting Brand Response</option>
          </select>
        </div>

        {/* Active Filter Tags */}
        <div className="flex items-center justify-between text-xs text-brand-muted pt-1 border-t border-brand-border/40">
          <div>
            Showing <strong className="text-brand-dark">{filteredReviews.length}</strong> of {totalReviewsCount} verified reviews
          </div>
          {(searchQuery || ratingFilter !== 'all' || proofTypeFilter !== 'all' || responseFilter !== 'all') && (
            <button
              onClick={() => {
                setSearchQuery('');
                setRatingFilter('all');
                setProofTypeFilter('all');
                setResponseFilter('all');
              }}
              className="text-xs text-[#111312] hover:underline font-bold"
            >
              Reset Filters
            </button>
          )}
        </div>
      </Card>

      {/* Reviews Stream */}
      <div className="space-y-5">
        {filteredReviews.length === 0 ? (
          <Card className="p-12 text-center space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-[#F4F3EF] text-brand-muted flex items-center justify-center mx-auto border border-[#DCDAD4]">
              <MessageSquareHeart className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-brand-dark">No verified customer reviews match your filters</h3>
            <p className="text-xs text-brand-muted max-w-sm mx-auto">
              Try adjusting your search query, proof type filter, or rating selection to view more verified customer reviews.
            </p>
          </Card>
        ) : (
          filteredReviews.map((rev) => {
            const proofBadge = getProofTypeBadge(rev.verifiedProof?.type);
            const ProofIcon = proofBadge.icon;

            return (
              <Card key={rev.id} className="p-5 space-y-4 border border-brand-border hover:border-[#111312]/40 transition-all bg-white">
                
                {/* Header: Customer Info, Verification Badges, Actions */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-brand-border/60">
                  <div className="flex items-start gap-3">
                    <div className="w-11 h-11 rounded-2xl bg-[#111312] text-[#FBF5A5] flex items-center justify-center font-extrabold text-sm border border-[#2B2D2C] shrink-0">
                      {rev.userName.slice(0, 1)}
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h4 className="text-sm font-bold text-brand-dark">{rev.userName}</h4>
                        {rev.userPhoneMasked && (
                          <span className="text-[11px] text-brand-muted font-mono">({rev.userPhoneMasked})</span>
                        )}
                        {rev.isPhoneVerified && (
                          <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-bold border border-emerald-200">
                            <CheckCircle2 className="w-2.5 h-2.5" /> Phone OTP Verified
                          </span>
                        )}
                        <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 font-bold border border-teal-200">
                          <ShieldCheck className="w-2.5 h-2.5" /> Verified Customer Only
                        </span>
                      </div>

                      {/* Stars & Timestamp */}
                      <div className="flex items-center gap-2 mt-1">
                        <div className="flex items-center gap-0.5 text-amber-500">
                          {[...Array(5)].map((_, i) => (
                            <Star
                              key={i}
                              className={`w-3.5 h-3.5 ${i < rev.rating ? 'fill-amber-400 text-amber-400' : 'text-gray-300'}`}
                            />
                          ))}
                        </div>
                        <span className="text-[11px] font-bold text-brand-dark">{rev.rating}.0 / 5.0</span>
                        <span className="text-[10px] text-brand-muted">•</span>
                        <span className="text-[11px] text-brand-muted flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {new Date(rev.createdAt).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Actions: Reply Button & Proof Inspector Button */}
                  <div className="flex items-center gap-2 self-start sm:self-center">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => handleOpenProofInspector(rev)}
                      leftIcon={<Eye className="w-3.5 h-3.5 text-[#111312]" />}
                    >
                      Inspect Proof
                    </Button>
                    <Button 
                      variant={rev.brandResponse ? 'secondary' : 'primary'}
                      size="sm" 
                      onClick={() => handleOpenReply(rev)} 
                      leftIcon={<Reply className="w-3.5 h-3.5" />}
                    >
                      {rev.brandResponse ? 'Edit Response' : 'Reply as Brand'}
                    </Button>
                  </div>
                </div>

                {/* Product/Service Purchased Tag */}
                {rev.verifiedProof?.productOrServicePurchased && (
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-brand-muted font-medium">Purchased Product / Service:</span>
                    <span className="font-bold text-brand-dark px-2.5 py-0.5 rounded-lg bg-brand-surface border border-brand-border">
                      {rev.verifiedProof.productOrServicePurchased}
                    </span>
                    {rev.verifiedProof.orderAmount && (
                      <span className="text-emerald-700 font-extrabold text-[11px] px-2 py-0.5 rounded-md bg-emerald-50 border border-emerald-200">
                        {rev.verifiedProof.orderAmount}
                      </span>
                    )}
                  </div>
                )}

                {/* Review Content */}
                <div>
                  <h3 className="text-base font-bold text-brand-dark">{rev.title}</h3>
                  <p className="text-xs sm:text-sm text-brand-muted mt-1 leading-relaxed">{rev.comment}</p>
                </div>

                {/* Verified Proof Banner Box */}
                {rev.verifiedProof && (
                  <div className="p-3.5 rounded-2xl bg-[#F8F7F4] border border-[#E2E1DC] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-start sm:items-center gap-2.5">
                      <div className="p-2 rounded-xl bg-white border border-[#DCDAD4] shrink-0 shadow-xs">
                        <ProofIcon className="w-4 h-4 text-[#111312]" />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${proofBadge.color}`}>
                            {proofBadge.label}
                          </span>
                          <span className="text-xs font-mono font-bold text-brand-dark truncate">
                            Ref: {rev.verifiedProof.referenceId}
                          </span>
                        </div>
                        <div className="text-[11px] text-brand-muted mt-0.5 flex items-center gap-1.5 truncate">
                          <FileText className="w-3 h-3 text-brand-muted shrink-0" />
                          <span className="truncate">{rev.verifiedProof.proofFileName}</span>
                          <span>•</span>
                          <span className="text-emerald-700 font-semibold">Proof Score: {rev.verifiedProof.proofScore}% Validated</span>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => handleOpenProofInspector(rev)}
                      className="text-xs text-[#111312] hover:underline font-bold flex items-center gap-1 shrink-0"
                    >
                      <span>View Proof Certificate</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </div>
                )}

                {/* Official Brand Response */}
                {rev.brandResponse && (
                  <div className="p-4 rounded-2xl bg-white border border-[#E2E1DC] space-y-2 border-l-4 border-l-[#111312] mt-2 shadow-sm">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs">
                      <div className="flex items-center gap-1.5 font-bold text-[#111312]">
                        <ShieldCheck className="w-4 h-4 text-[#111312] shrink-0" />
                        <span>Official Response from {rev.brandResponse.responderName}</span>
                        <span className="text-[10px] text-brand-muted font-normal">({rev.brandResponse.responderRole})</span>
                      </div>
                      <span className="text-[10px] text-brand-muted">
                        Responded {new Date(rev.brandResponse.respondedAt).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}
                      </span>
                    </div>
                    <p className="text-xs text-brand-dark leading-relaxed">
                      {rev.brandResponse.response}
                    </p>
                  </div>
                )}

                {/* Footer: Upvotes & Triage Status */}
                <div className="flex items-center justify-between pt-2 text-xs text-brand-muted">
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center gap-1 text-brand-dark font-medium bg-[#F4F3EF] px-2.5 py-1 rounded-xl border border-[#DCDAD4]">
                      <ThumbsUp className="w-3.5 h-3.5 text-[#111312]" />
                      <span>{rev.upvotesCount} customers found this verified review helpful</span>
                    </span>
                  </div>
                  <div className="text-[11px] text-brand-muted">
                    ID: <span className="font-mono">{rev.id}</span>
                  </div>
                </div>

              </Card>
            );
          })
        )}
      </div>

      {/* Proof Document & Certificate Inspector Modal */}
      <Modal
        isOpen={proofModalOpen}
        onClose={() => setProofModalOpen(false)}
        title="Verified Customer Proof & Certificate Inspector"
        description="Inspect customer purchase proof, receipt attachment, cryptographic hash, and verification certificate."
        maxWidth="lg"
      >
        {inspectingReview && inspectingReview.verifiedProof && (
          <div className="space-y-4">
            
            {/* Certificate Header Banner */}
            <div className="p-4 rounded-xl bg-[#EAF5F0] border border-[#C3E4D6] flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-emerald-600 text-white flex items-center justify-center font-bold shadow-soft">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-extrabold text-brand-dark flex items-center gap-1.5">
                    Cryptographically Verified Authentic Review
                  </h4>
                  <p className="text-[11px] text-emerald-800 font-medium">
                    Validated by BrandShield Customer Proof Node • Anti-Fraud Score: {inspectingReview.verifiedProof.proofScore}%
                  </p>
                </div>
              </div>
              <Badge variant="status" status="verified">Verified Customer Only</Badge>
            </div>

            {/* Proof Metadata Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-2xl bg-brand-surface-light border border-brand-border space-y-1">
                <span className="text-brand-muted font-medium">Customer Full Name & OTP:</span>
                <p className="font-bold text-brand-dark flex items-center gap-1.5">
                  <UserCheck className="w-3.5 h-3.5 text-emerald-600" />
                  {inspectingReview.userName} <span className="text-brand-muted font-mono">({inspectingReview.userPhoneMasked})</span>
                </p>
                <p className="text-[10px] text-emerald-700 font-semibold">✓ SMS One-Time Passcode Authenticated</p>
              </div>

              <div className="p-3 rounded-2xl bg-brand-surface-light border border-brand-border space-y-1">
                <span className="text-brand-muted font-medium">Proof Reference ID:</span>
                <p className="font-bold text-brand-dark font-mono flex items-center gap-1.5">
                  <Receipt className="w-3.5 h-3.5 text-[#111312]" />
                  {inspectingReview.verifiedProof.referenceId}
                </p>
                <p className="text-[10px] text-brand-muted">Amount: {inspectingReview.verifiedProof.orderAmount || 'Verified Service Agreement'}</p>
              </div>

              <div className="p-3 rounded-2xl bg-brand-surface-light border border-brand-border space-y-1">
                <span className="text-brand-muted font-medium">Product / Plan / Subscription:</span>
                <p className="font-bold text-brand-dark">
                  {inspectingReview.verifiedProof.productOrServicePurchased}
                </p>
              </div>

              <div className="p-3 rounded-2xl bg-brand-surface-light border border-brand-border space-y-1">
                <span className="text-brand-muted font-medium">Verification Timestamp:</span>
                <p className="font-bold text-brand-dark flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-brand-muted" />
                  {new Date(inspectingReview.verifiedProof.verificationTimestamp).toLocaleString()}
                </p>
              </div>
            </div>

            {/* Cryptographic SHA-256 Hash Card */}
            {inspectingReview.verifiedProof.cryptographicHash && (
              <div className="p-3 rounded-2xl bg-[#F4F3EF] border border-[#DCDAD4] space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-brand-dark flex items-center gap-1">
                    <Hash className="w-3.5 h-3.5 text-[#111312]" />
                    Cryptographic Proof SHA-256 Digest
                  </span>
                  <button
                    onClick={() => handleCopyHash(inspectingReview.verifiedProof?.cryptographicHash || '')}
                    className="text-[11px] font-bold text-[#111312] hover:underline flex items-center gap-1"
                  >
                    {copiedHash ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedHash ? 'Copied' : 'Copy Hash'}</span>
                  </button>
                </div>
                <div className="font-mono text-[10px] text-brand-muted bg-white p-2 rounded-xl border border-brand-border break-all select-all">
                  {inspectingReview.verifiedProof.cryptographicHash}
                </div>
              </div>
            )}

            {/* Proof Document Screenshot Preview */}
            {inspectingReview.verifiedProof.proofFileUrl && (
              <div className="space-y-1.5">
                <span className="text-xs font-bold text-brand-dark flex items-center gap-1">
                  <FileText className="w-3.5 h-3.5 text-[#111312]" />
                  Proof Document Snapshot ({inspectingReview.verifiedProof.proofFileName})
                </span>
                <div className="relative rounded-2xl overflow-hidden border border-brand-border max-h-56 bg-brand-dark/5 flex items-center justify-center">
                  <img
                    src={inspectingReview.verifiedProof.proofFileUrl}
                    alt="Proof Attachment"
                    className="w-full h-auto object-cover max-h-56"
                  />
                  <div className="absolute top-2 right-2 px-2.5 py-1 rounded-lg bg-[#111312] text-white text-[10px] font-mono border border-white/20">
                    Verified Digital Artifact
                  </div>
                </div>
              </div>
            )}

            {/* Modal Actions */}
            <div className="flex justify-end gap-3 pt-3 border-t border-brand-border/60">
              <Button variant="outline" onClick={() => setProofModalOpen(false)}>
                Close Inspector
              </Button>
              <Button 
                variant="primary" 
                onClick={() => {
                  setProofModalOpen(false);
                  handleOpenReply(inspectingReview);
                }}
                leftIcon={<Reply className="w-3.5 h-3.5" />}
              >
                Reply to Review
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Reply Composer Modal */}
      <Modal
        isOpen={replyModalOpen}
        onClose={() => setReplyModalOpen(false)}
        title="Official Verified Brand Owner Response"
        description="Publish an official brand response that will be publicly displayed on the customer-facing verified review feed."
        maxWidth="md"
      >
        <form onSubmit={handleSendResponse} className="space-y-4">
          <div className="p-3 rounded-2xl bg-brand-surface-light border border-brand-border text-xs">
            <span className="font-bold text-brand-dark">Responding to customer review by {selectedReview?.userName}:</span>
            <p className="text-brand-muted italic mt-1 font-serif">"{selectedReview?.title}"</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Input
              label="Responder Name"
              value={responderName}
              onChange={(e) => setResponderName(e.target.value)}
              placeholder="e.g. Elena Rostova"
              required
            />
            <Input
              label="Responder Title / Role"
              value={responderRole}
              onChange={(e) => setResponderRole(e.target.value)}
              placeholder="e.g. Brand Protection Lead"
              required
            />
          </div>

          <Textarea
            label="Official Response Message"
            value={responseText}
            onChange={(e) => setResponseText(e.target.value)}
            placeholder="Thank you for your verified feedback! Our fraud intelligence team has..."
            rows={4}
            required
          />

          <div className="flex items-center gap-2 p-2.5 rounded-xl bg-[#F4F3EF] border border-[#DCDAD4] text-xs text-[#111312]">
            <ShieldCheck className="w-4 h-4 text-[#111312] shrink-0" />
            <span>This response will carry the official verified brand security seal.</span>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-brand-border/60">
            <Button type="button" variant="outline" onClick={() => setReplyModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={isSubmittingReply} leftIcon={<Sparkles className="w-3.5 h-3.5" />}>
              Publish Official Response
            </Button>
          </div>
        </form>
      </Modal>

    </div>
  );
};
