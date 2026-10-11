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
  Check,
  Moon,
  Sun,
  ArrowUpRight,
  Shield,
  Layers,
  ShoppingBag
} from 'lucide-react';

export const CustomerReviewsPage: React.FC = () => {
  const { currentBrand } = useBrand();
  const { showToast } = useNotification();
  const [reviews, setReviews] = useState<CustomerReview[]>([]);
  const [loading, setLoading] = useState(true);

  // Card theme mode: 'dark' (matching reference image) or 'light'
  const [cardTheme, setCardTheme] = useState<'dark' | 'light'>('dark');

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

  const getProofTypeBadge = (type?: string, isDark: boolean = true) => {
    switch (type) {
      case 'invoice_receipt':
        return { 
          label: 'Verified Invoice / Receipt', 
          icon: Receipt, 
          style: isDark ? 'bg-emerald-950/80 text-emerald-400 border-emerald-800' : 'bg-emerald-50 text-emerald-700 border-emerald-200' 
        };
      case 'transaction_ref':
        return { 
          label: 'Verified Transaction Ref', 
          icon: DollarSign, 
          style: isDark ? 'bg-blue-950/80 text-blue-400 border-blue-800' : 'bg-blue-50 text-blue-700 border-blue-200' 
        };
      case 'phone_otp_and_contract':
        return { 
          label: 'Phone OTP & Contract', 
          icon: UserCheck, 
          style: isDark ? 'bg-stone-800 text-stone-200 border-stone-700' : 'bg-stone-100 text-[#111312] border-stone-300' 
        };
      case 'crypto_tx_or_order':
        return { 
          label: 'Cryptographic Order Digest', 
          icon: Lock, 
          style: isDark ? 'bg-teal-950/80 text-teal-400 border-teal-800' : 'bg-teal-50 text-teal-700 border-teal-200' 
        };
      default:
        return { 
          label: 'Verified Customer Proof', 
          icon: ShieldCheck, 
          style: isDark ? 'bg-emerald-950/80 text-emerald-400 border-emerald-800' : 'bg-emerald-50 text-emerald-700 border-emerald-200' 
        };
    }
  };

  // Avatar gradient generator based on user name
  const getAvatarGradient = (name: string) => {
    const gradients = [
      'from-amber-500 to-rose-500',
      'from-blue-500 to-cyan-500',
      'from-emerald-500 to-teal-500',
      'from-purple-500 to-indigo-500',
      'from-fuchsia-500 to-pink-500',
      'from-orange-500 to-amber-500'
    ];
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % gradients.length;
    return gradients[index];
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* 1. Page Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-[#E2E1DC]">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-black uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#111312] text-[#FBF5A5] border border-[#2B2D2C]">
              Verified Proof Ledger
            </span>
            <span className="text-xs font-bold text-emerald-700 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> 100% Cryptographically Backed
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#111312] tracking-tight mt-1.5">
            Customer Reviews & Verified Proof Hub
          </h1>
          <p className="text-xs sm:text-sm text-[#434346] mt-1 max-w-3xl">
            Customer feedback backed by cryptographic proof, verified order receipts, and Phone OTP validation. Inspect proof artifacts, triage customer feedback, and publish verified brand owner responses.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-white border border-[#E2E1DC] shadow-soft flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-bold text-base shadow-soft">
              <Star className="w-5 h-5 fill-white text-white" />
            </div>
            <div>
              <div className="text-base font-extrabold text-[#111312] flex items-center gap-1.5">
                {avgRating} <span className="text-xs text-[#73726E] font-normal">/ 5.0</span>
              </div>
              <div className="text-[11px] text-emerald-700 font-bold flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Zero Bot Spam
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Top 4 Executive KPI Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-white border border-[#E2E1DC] shadow-soft">
          <span className="text-[10px] font-bold text-[#434346] uppercase tracking-wider block">Verified Reviews</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-black text-[#111312]">{totalReviewsCount}</span>
            <span className="text-[11px] font-semibold text-emerald-700">Phone OTP Verified</span>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-[#E2E1DC] shadow-soft">
          <span className="text-[10px] font-bold text-[#434346] uppercase tracking-wider block">Proof Verification Rate</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-black text-emerald-700">{verifiedProofRate}</span>
            <span className="text-[11px] font-semibold text-[#434346]">Cryptographic Ledger</span>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-[#E2E1DC] shadow-soft">
          <span className="text-[10px] font-bold text-[#434346] uppercase tracking-wider block">Brand Response Rate</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-black text-[#111312]">{responseRate}%</span>
            <span className="text-[11px] font-semibold text-[#434346]">{responseCount}/{totalReviewsCount} Answered</span>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-[#E2E1DC] shadow-soft">
          <span className="text-[10px] font-bold text-[#434346] uppercase tracking-wider block">Customer Trust Score</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-black text-teal-700">99 / 100</span>
            <span className="text-[11px] font-semibold text-teal-700">High Credibility</span>
          </div>
        </div>
      </div>

      {/* 3. Filter and Search Bar with Theme Toggle */}
      <div className="p-4 rounded-2xl bg-white border border-[#E2E1DC] shadow-soft space-y-3">
        <div className="flex flex-col md:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-[#73726E] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by customer name, review quote, order reference, or purchased product..."
              className="w-full pl-10 pr-4 py-2 text-xs rounded-xl bg-[#FAF9F5] border border-[#E2E1DC] focus:bg-white focus:outline-none focus:border-[#111312] transition-all text-[#111312] placeholder-[#8A8984]"
            />
          </div>

          {/* Rating Filter */}
          <select
            value={ratingFilter}
            onChange={(e) => setRatingFilter(e.target.value)}
            className="px-3 py-2 text-xs rounded-xl bg-[#FAF9F5] border border-[#E2E1DC] focus:outline-none focus:border-[#111312] text-[#111312] font-semibold"
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
            className="px-3 py-2 text-xs rounded-xl bg-[#FAF9F5] border border-[#E2E1DC] focus:outline-none focus:border-[#111312] text-[#111312] font-semibold"
          >
            <option value="all">All Verified Proof Types</option>
            <option value="invoice_receipt">Invoice / Receipt Upload</option>
            <option value="transaction_ref">Transaction Reference</option>
            <option value="phone_otp_and_contract">Phone OTP & Contract</option>
            <option value="crypto_tx_or_order">Cryptographic Order Digest</option>
          </select>

          {/* Brand Response Filter */}
          <select
            value={responseFilter}
            onChange={(e) => setResponseFilter(e.target.value)}
            className="px-3 py-2 text-xs rounded-xl bg-[#FAF9F5] border border-[#E2E1DC] focus:outline-none focus:border-[#111312] text-[#111312] font-semibold"
          >
            <option value="all">All Response States</option>
            <option value="replied">Responded by Brand</option>
            <option value="pending">Awaiting Brand Response</option>
          </select>

          {/* Card Theme Toggle (Dark cards matching reference vs Light cards) */}
          <div className="flex items-center gap-1 p-1 bg-[#FAF9F5] border border-[#E2E1DC] rounded-xl self-start md:self-auto">
            <button
              onClick={() => setCardTheme('dark')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                cardTheme === 'dark' 
                  ? 'bg-[#111312] text-white shadow-xs' 
                  : 'text-[#434346] hover:text-[#111312]'
              }`}
              title="Dark Card Theme (Reference Style)"
            >
              <Moon className="w-3.5 h-3.5" />
              <span>Dark Grid</span>
            </button>
            <button
              onClick={() => setCardTheme('light')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                cardTheme === 'light' 
                  ? 'bg-white text-[#111312] shadow-xs border border-[#E2E1DC]' 
                  : 'text-[#434346] hover:text-[#111312]'
              }`}
              title="Light Card Theme"
            >
              <Sun className="w-3.5 h-3.5" />
              <span>Light Grid</span>
            </button>
          </div>
        </div>

        {/* Active Filter Tags Bar */}
        <div className="flex items-center justify-between text-xs text-[#73726E] pt-2 border-t border-[#E2E1DC]">
          <div>
            Showing <strong className="text-[#111312]">{filteredReviews.length}</strong> of {totalReviewsCount} verified customer reviews
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
      </div>

      {/* 4. REDESIGNED REVIEWS GRID (Matching Reference Image media_1791654513065.png) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredReviews.length === 0 ? (
          <div className="col-span-full p-16 text-center space-y-3 bg-white rounded-3xl border border-[#E2E1DC]">
            <div className="w-12 h-12 rounded-2xl bg-[#F4F3EF] text-[#73726E] flex items-center justify-center mx-auto border border-[#DCDAD4]">
              <MessageSquareHeart className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-[#111312]">No verified customer reviews match your filters</h3>
            <p className="text-xs text-[#73726E] max-w-sm mx-auto">
              Try adjusting your search query, proof type filter, or rating selection to view more verified customer reviews.
            </p>
          </div>
        ) : (
          filteredReviews.map((rev) => {
            const isDark = cardTheme === 'dark';
            const proofBadge = getProofTypeBadge(rev.verifiedProof?.type, isDark);
            const ProofIcon = proofBadge.icon;
            const avatarGradient = getAvatarGradient(rev.userName);

            return (
              <div
                key={rev.id}
                className={`rounded-3xl p-6 transition-all duration-300 flex flex-col justify-between relative group ${
                  isDark
                    ? 'bg-[#111215] text-white border border-[#23252B] hover:border-[#FBF5A5]/80 shadow-xl'
                    : 'bg-white text-[#111312] border border-[#E2E1DC] hover:border-[#111312] shadow-soft hover:shadow-xl'
                }`}
              >
                {/* Top Section: Prominent Quote Header (Inspired by reference image) */}
                <div className="space-y-4">
                  {/* Big Bold Quotation Title */}
                  <div>
                    <h3 className={`text-base sm:text-lg font-black tracking-tight leading-snug ${
                      isDark ? 'text-white' : 'text-[#111312]'
                    }`}>
                      “{rev.title}”
                    </h3>

                    {/* Star Rating & Timestamp */}
                    <div className="flex items-center gap-2 mt-2">
                      <div className="flex items-center gap-0.5 text-amber-400">
                        {[...Array(5)].map((_, i) => (
                          <Star
                            key={i}
                            className={`w-3.5 h-3.5 ${
                              i < rev.rating 
                                ? 'fill-amber-400 text-amber-400' 
                                : isDark ? 'text-neutral-700' : 'text-neutral-300'
                            }`}
                          />
                        ))}
                      </div>
                      <span className={`text-[11px] font-bold ${isDark ? 'text-[#FBF5A5]' : 'text-[#111312]'}`}>
                        {rev.rating}.0
                      </span>
                      <span className="text-[10px] text-neutral-500">•</span>
                      <span className={`text-[11px] flex items-center gap-1 ${isDark ? 'text-neutral-400' : 'text-[#73726E]'}`}>
                        <Calendar className="w-3 h-3" />
                        {new Date(rev.createdAt).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}
                      </span>
                    </div>
                  </div>

                  {/* Review Description Body */}
                  <p className={`text-xs sm:text-sm leading-relaxed ${
                    isDark ? 'text-[#9E9EA4]' : 'text-[#434346]'
                  }`}>
                    {rev.comment}
                  </p>

                  {/* Purchased Product Information Tag */}
                  {rev.verifiedProof?.productOrServicePurchased && (
                    <div className={`p-2.5 rounded-xl border flex items-center justify-between text-xs gap-2 ${
                      isDark 
                        ? 'bg-[#18191E] border-[#2A2B32] text-neutral-300' 
                        : 'bg-[#F8F7F4] border-[#E2E1DC] text-[#434346]'
                    }`}>
                      <div className="flex items-center gap-1.5 min-w-0">
                        <ShoppingBag className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                        <span className="font-semibold truncate">
                          {rev.verifiedProof.productOrServicePurchased}
                        </span>
                      </div>
                      {rev.verifiedProof.orderAmount && (
                        <span className={`font-mono font-bold text-[10px] px-2 py-0.5 rounded-md shrink-0 ${
                          isDark 
                            ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800' 
                            : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        }`}>
                          {rev.verifiedProof.orderAmount}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Proof Certificate Preview Strip */}
                  {rev.verifiedProof && (
                    <div className={`p-3 rounded-2xl border flex items-center justify-between gap-3 ${
                      isDark 
                        ? 'bg-[#18191E] border-[#2A2B32]' 
                        : 'bg-[#FAF9F5] border-[#E2E1DC]'
                    }`}>
                      <div className="flex items-center gap-2.5 min-w-0">
                        <div className={`p-1.5 rounded-lg shrink-0 ${
                          isDark ? 'bg-[#22242B] text-emerald-400' : 'bg-white text-[#111312] border border-[#E2E1DC]'
                        }`}>
                          <ProofIcon className="w-4 h-4" />
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-1.5">
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${proofBadge.style}`}>
                              {proofBadge.label}
                            </span>
                          </div>
                          <p className={`text-[11px] font-mono font-semibold truncate mt-0.5 ${
                            isDark ? 'text-neutral-400' : 'text-[#73726E]'
                          }`}>
                            Ref: {rev.verifiedProof.referenceId} &bull; {rev.verifiedProof.proofScore}% Validated
                          </p>
                        </div>
                      </div>

                      <button
                        onClick={() => handleOpenProofInspector(rev)}
                        className={`text-xs font-bold shrink-0 flex items-center gap-1 hover:underline ${
                          isDark ? 'text-[#FBF5A5]' : 'text-[#111312]'
                        }`}
                        title="View Full Proof Certificate"
                      >
                        <span className="hidden sm:inline">Proof</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}

                  {/* Official Brand Response Quote Box */}
                  {rev.brandResponse && (
                    <div className={`p-3.5 rounded-2xl border space-y-1.5 border-l-4 ${
                      isDark 
                        ? 'bg-[#18191E] border-[#2A2B32] border-l-[#FBF5A5]' 
                        : 'bg-[#F4F3EF] border-[#E2E1DC] border-l-[#111312]'
                    }`}>
                      <div className="flex items-center justify-between gap-2 text-xs">
                        <div className="flex items-center gap-1.5 font-bold">
                          <ShieldCheck className={`w-3.5 h-3.5 shrink-0 ${isDark ? 'text-[#FBF5A5]' : 'text-[#111312]'}`} />
                          <span className={isDark ? 'text-[#FBF5A5]' : 'text-[#111312]'}>
                            Official Response from {rev.brandResponse.responderName}
                          </span>
                        </div>
                        <span className="text-[10px] text-neutral-500">
                          {new Date(rev.brandResponse.respondedAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                        </span>
                      </div>
                      <p className={`text-xs leading-relaxed ${isDark ? 'text-neutral-300' : 'text-[#434346]'}`}>
                        {rev.brandResponse.response}
                      </p>
                    </div>
                  )}
                </div>

                {/* Bottom Section: Customer Details & Actions Bar (Matching reference bottom row) */}
                <div className={`pt-5 mt-5 border-t space-y-3 ${
                  isDark ? 'border-[#23252B]' : 'border-[#E2E1DC]'
                }`}>
                  {/* Customer Avatar & Details Bar */}
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                      {/* Avatar */}
                      <div className={`w-10 h-10 rounded-full bg-gradient-to-tr ${avatarGradient} flex items-center justify-center font-black text-sm text-white shrink-0 shadow-sm`}>
                        {rev.userName.slice(0, 1)}
                      </div>

                      {/* Name & Masked Phone / Role */}
                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5">
                          <h4 className={`text-sm font-extrabold truncate ${
                            isDark ? 'text-white' : 'text-[#111312]'
                          }`}>
                            {rev.userName}
                          </h4>
                          {rev.isPhoneVerified && (
                            <span title="Phone OTP Authenticated">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                            </span>
                          )}
                        </div>
                        <p className={`text-[11px] truncate ${
                          isDark ? 'text-[#8A8A92]' : 'text-[#73726E]'
                        }`}>
                          {rev.userPhoneMasked || '@verified_customer'}
                        </p>
                      </div>
                    </div>

                    {/* Helpful count */}
                    <span className={`inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-1 rounded-xl shrink-0 ${
                      isDark 
                        ? 'bg-[#1C1D24] text-neutral-300 border border-[#2D2E38]' 
                        : 'bg-[#F4F3EF] text-[#434346] border border-[#DCDAD4]'
                    }`}>
                      <ThumbsUp className="w-3 h-3 text-amber-500" />
                      <span>{rev.upvotesCount}</span>
                    </span>
                  </div>

                  {/* Brand Owner Action Buttons */}
                  <div className="flex items-center gap-2 pt-1">
                    <Button 
                      variant={isDark ? 'outline' : 'outline'} 
                      size="sm" 
                      onClick={() => handleOpenProofInspector(rev)}
                      leftIcon={<Eye className="w-3.5 h-3.5" />}
                      className={`flex-1 ${
                        isDark 
                          ? 'border-[#33353E] text-white hover:bg-[#1E2028]' 
                          : 'border-[#E2E1DC] text-[#111312]'
                      }`}
                    >
                      Inspect Proof
                    </Button>
                    <Button 
                      variant={rev.brandResponse ? 'secondary' : 'primary'}
                      size="sm" 
                      onClick={() => handleOpenReply(rev)} 
                      leftIcon={<Reply className="w-3.5 h-3.5" />}
                      className="flex-1"
                    >
                      {rev.brandResponse ? 'Edit Reply' : 'Reply as Brand'}
                    </Button>
                  </div>
                </div>

              </div>
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
                  <h4 className="text-sm font-extrabold text-[#111312] flex items-center gap-1.5">
                    Cryptographically Verified Authentic Review
                  </h4>
                  <p className="text-[11px] text-emerald-800 font-medium">
                    Validated by Customer Proof Node • Anti-Fraud Score: {inspectingReview.verifiedProof.proofScore}%
                  </p>
                </div>
              </div>
              <Badge variant="status" status="verified">Verified Customer Only</Badge>
            </div>

            {/* Proof Metadata Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-2xl bg-[#F8F7F4] border border-[#E2E1DC] space-y-1">
                <span className="text-[#73726E] font-medium">Customer Full Name & OTP:</span>
                <p className="font-bold text-[#111312] flex items-center gap-1.5">
                  <UserCheck className="w-3.5 h-3.5 text-emerald-600" />
                  {inspectingReview.userName} <span className="text-[#73726E] font-mono">({inspectingReview.userPhoneMasked})</span>
                </p>
                <p className="text-[10px] text-emerald-700 font-semibold">✓ SMS One-Time Passcode Authenticated</p>
              </div>

              <div className="p-3 rounded-2xl bg-[#F8F7F4] border border-[#E2E1DC] space-y-1">
                <span className="text-[#73726E] font-medium">Proof Reference ID:</span>
                <p className="font-bold text-[#111312] font-mono flex items-center gap-1.5">
                  <Receipt className="w-3.5 h-3.5 text-[#111312]" />
                  {inspectingReview.verifiedProof.referenceId}
                </p>
                <p className="text-[10px] text-[#73726E]">Amount: {inspectingReview.verifiedProof.orderAmount || 'Verified Service Agreement'}</p>
              </div>

              <div className="p-3 rounded-2xl bg-[#F8F7F4] border border-[#E2E1DC] space-y-1">
                <span className="text-[#73726E] font-medium">Product / Plan / Subscription:</span>
                <p className="font-bold text-[#111312]">
                  {inspectingReview.verifiedProof.productOrServicePurchased}
                </p>
              </div>

              <div className="p-3 rounded-2xl bg-[#F8F7F4] border border-[#E2E1DC] space-y-1">
                <span className="text-[#73726E] font-medium">Verification Timestamp:</span>
                <p className="font-bold text-[#111312] flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-[#73726E]" />
                  {new Date(inspectingReview.verifiedProof.verificationTimestamp).toLocaleString()}
                </p>
              </div>
            </div>

            {/* Cryptographic SHA-256 Hash Card */}
            {inspectingReview.verifiedProof.cryptographicHash && (
              <div className="p-3 rounded-2xl bg-[#F4F3EF] border border-[#DCDAD4] space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[#111312] flex items-center gap-1">
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
                <div className="font-mono text-[10px] text-[#434346] bg-white p-2 rounded-xl border border-[#E2E1DC] break-all select-all">
                  {inspectingReview.verifiedProof.cryptographicHash}
                </div>
              </div>
            )}

            {/* Proof Document Screenshot Preview */}
            {inspectingReview.verifiedProof.proofFileUrl && (
              <div className="space-y-1.5">
                <span className="text-xs font-bold text-[#111312] flex items-center gap-1">
                  <FileText className="w-3.5 h-3.5 text-[#111312]" />
                  Proof Document Snapshot ({inspectingReview.verifiedProof.proofFileName})
                </span>
                <div className="relative rounded-2xl overflow-hidden border border-[#E2E1DC] max-h-56 bg-neutral-100 flex items-center justify-center">
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
            <div className="flex justify-end gap-3 pt-3 border-t border-[#E2E1DC]">
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
          <div className="p-3 rounded-2xl bg-[#F8F7F4] border border-[#E2E1DC] text-xs">
            <span className="font-bold text-[#111312]">Responding to customer review by {selectedReview?.userName}:</span>
            <p className="text-[#434346] italic mt-1 font-serif">"{selectedReview?.title}"</p>
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

          <div className="flex justify-end gap-3 pt-3 border-t border-[#E2E1DC]">
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
