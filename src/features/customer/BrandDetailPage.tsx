import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { brandService, reviewService } from '../../services/api';
import { BrandProfile, CustomerReview } from '../../types';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Input, Textarea } from '../../components/ui/Input';
import { useNotification } from '../../context/NotificationContext';
import { useAuth } from '../../context/AuthContext';
import { 
  ShieldCheck, 
  Globe2, 
  Share2, 
  Smartphone, 
  Star, 
  AlertTriangle, 
  ThumbsUp, 
  ArrowLeft, 
  CheckCircle2, 
  ExternalLink,
  MessageSquare
} from 'lucide-react';
import confetti from 'canvas-confetti';

export const BrandDetailPage: React.FC = () => {
  const { brandSlug } = useParams<{ brandSlug: string }>();
  const { user } = useAuth();
  const { showToast } = useNotification();
  
  const [brand, setBrand] = useState<BrandProfile | null>(null);
  const [reviews, setReviews] = useState<CustomerReview[]>([]);
  const [rating, setRating] = useState(5);
  const [productPurchased, setProductPurchased] = useState('');
  const [proofRefId, setProofRefId] = useState('');
  const [proofType, setProofType] = useState<string>('invoice_receipt');
  const [orderAmount, setOrderAmount] = useState('');
  const [reviewTitle, setReviewTitle] = useState('');
  const [reviewComment, setReviewComment] = useState('');
  const [isSubmittingReview, setIsSubmittingReview] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      try {
        if (brandSlug) {
          const b = await brandService.getBrandBySlug(brandSlug);
          setBrand(b);
          if (b) {
            const revList = await reviewService.getReviews(b.id);
            setReviews(revList);
          }
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [brandSlug]);

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!brand || !reviewTitle || !reviewComment) return;

    setIsSubmittingReview(true);
    try {
      const newRev = await reviewService.submitReview({
        brandId: brand.id,
        brandName: brand.name,
        userId: user?.id || 'user_cust_1',
        userName: user?.name || 'Verified Customer',
        rating,
        title: reviewTitle,
        comment: reviewComment,
        isCustomerVerifiedOnly: true,
        verifiedProof: {
          type: (proofType as any) || 'invoice_receipt',
          referenceId: proofRefId.trim() || `INV-${Date.now().toString().slice(-6)}`,
          proofFileName: `${brand.name.replace(/\s+/g, '_')}_Verified_Receipt.pdf`,
          proofFileUrl: 'https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=600&auto=format&fit=crop&q=80',
          verificationTimestamp: new Date().toISOString(),
          verificationStatus: 'verified_authentic',
          proofScore: 99,
          orderAmount: orderAmount.trim() || '$1,250.00',
          productOrServicePurchased: productPurchased.trim() || `${brand.name} Commercial Protection Plan`,
          cryptographicHash: `0x${Array.from({length: 64}, () => Math.floor(Math.random() * 16).toString(16)).join('')}`
        }
      });

      setReviews([newRev, ...reviews]);
      setReviewTitle('');
      setReviewComment('');
      setProductPurchased('');
      setProofRefId('');
      setOrderAmount('');
      confetti({ particleCount: 50, spread: 60 });
      showToast({ type: 'success', title: 'Verified Review Submitted', message: 'Thank you! Your verified proof review is now visible in the Brand Owner Portal.' });
    } catch (err) {
      showToast({ type: 'error', title: 'Submission Failed', message: 'Please try again.' });
    } finally {
      setIsSubmittingReview(false);
    }
  };

  if (isLoading || !brand) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="w-10 h-10 border-3 border-[#111312] border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-brand-muted">Loading brand profile...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Back Link */}
      <Link
        to="/customer/brands"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-muted hover:text-[#111312] transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Verified Brands</span>
      </Link>

      {/* Brand Hero Card */}
      <Card className="bg-white border-[#E2E1DC]">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            <img
              src={brand.logoUrl}
              alt={brand.name}
              className="w-20 h-20 rounded-3xl object-cover border border-brand-border shadow-soft"
            />
            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-2xl font-extrabold text-brand-dark">{brand.name}</h1>
                <Badge variant="status" status={brand.verificationStatus} />
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#F4F3EF] text-[#111312] font-bold border border-[#DCDAD4]">
                  {brand.industry}
                </span>
              </div>
              <p className="text-xs text-brand-muted max-w-xl">{brand.description}</p>
              <a
                href={brand.officialWebsite}
                target="_blank"
                rel="noreferrer"
                className="text-xs font-mono font-bold text-[#111312] hover:underline inline-flex items-center gap-1 pt-1"
              >
                <Globe2 className="w-3.5 h-3.5" />
                <span>{brand.officialWebsite}</span>
                <ExternalLink className="w-3 h-3 ml-0.5" />
              </a>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3">
            <Link to="/customer/report" state={{ brandId: brand.id, brandName: brand.name }}>
              <Button
                variant="danger"
                size="sm"
                leftIcon={<AlertTriangle className="w-4 h-4" />}
              >
                Report Scam Targeting {brand.name}
              </Button>
            </Link>
          </div>
        </div>
      </Card>

      {/* Verified Channels List */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-brand-dark">Official Authenticated Channels</h3>
        <p className="text-xs text-brand-muted">Only trust communications originating from these verified assets.</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {brand.assets.map((asset) => (
            <div key={asset.id} className="p-4 rounded-2xl bg-white border border-brand-border shadow-sm flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-[#F4F3EF] text-[#111312] border border-[#E2E1DC]">
                  {asset.type === 'domain' ? <Globe2 className="w-4 h-4" /> :
                   asset.type === 'mobile_app' ? <Smartphone className="w-4 h-4" /> : <Share2 className="w-4 h-4" />}
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-brand-muted">{asset.type.replace('_', ' ')}</span>
                  <p className="text-xs font-bold text-brand-dark">{asset.value}</p>
                </div>
              </div>

              <span className="inline-flex items-center gap-1 text-[11px] text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                <CheckCircle2 className="w-3 h-3" /> Verified
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Reviews & Feedback Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Review Submission Form (5-cols) */}
        <div className="lg:col-span-5">
          <Card
            header={
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-[#111312]" />
                <h3 className="text-sm font-bold text-brand-dark">Write Feedback for {brand.name}</h3>
              </div>
            }
          >
            <form onSubmit={handleSubmitReview} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-brand-dark mb-1">Your Rating</label>
                <div className="flex items-center gap-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setRating(star)}
                      className="p-1 text-amber-400 hover:scale-110 transition-transform"
                    >
                      <Star className={`w-5 h-5 ${star <= rating ? 'fill-amber-400' : 'text-gray-300'}`} />
                    </button>
                  ))}
                  <span className="text-xs font-bold text-brand-muted ml-2">{rating} of 5 Stars</span>
                </div>
              </div>

              <Input
                label="Product / Service Purchased"
                value={productPurchased}
                onChange={(e) => setProductPurchased(e.target.value)}
                placeholder="e.g. Apex Corporate Account & Treasury Card"
                required
              />

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-brand-dark mb-1">Proof Type</label>
                  <select
                    value={proofType}
                    onChange={(e) => setProofType(e.target.value)}
                    className="w-full px-2.5 py-2 text-xs rounded-2xl bg-brand-surface-light border border-brand-border focus:outline-none text-brand-dark"
                  >
                    <option value="invoice_receipt">Invoice / Receipt</option>
                    <option value="transaction_ref">Transaction Ref</option>
                    <option value="phone_otp_and_contract">Phone OTP & Contract</option>
                    <option value="crypto_tx_or_order">Order ID / Tx</option>
                  </select>
                </div>

                <Input
                  label="Proof Reference ID"
                  value={proofRefId}
                  onChange={(e) => setProofRefId(e.target.value)}
                  placeholder="e.g. INV-2026-9912"
                  required
                />
              </div>

              <Input
                label="Review Headline"
                value={reviewTitle}
                onChange={(e) => setReviewTitle(e.target.value)}
                placeholder="e.g. Prompt fraud alert resolution"
                required
              />

              <Textarea
                label="Your Security Experience"
                value={reviewComment}
                onChange={(e) => setReviewComment(e.target.value)}
                placeholder="Share your experience interacting with this brand's official security perimeter..."
                required
              />

              <Button type="submit" className="w-full" isLoading={isSubmittingReview}>
                Upload Verified Feedback
              </Button>
            </form>
          </Card>
        </div>

        {/* Existing Reviews List (7-cols) */}
        <div className="lg:col-span-7 space-y-4">
          <h3 className="text-sm font-bold text-brand-dark">Community Reviews ({reviews.length})</h3>

          {reviews.map((rev) => (
            <Card key={rev.id} className="space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="text-xs font-bold text-brand-dark">{rev.userName}</h4>
                    {rev.isPhoneVerified && (
                      <span className="text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded-full border border-emerald-200">
                        Phone Verified
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1 text-amber-400 mt-0.5">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className={`w-3 h-3 ${i < rev.rating ? 'fill-amber-400' : 'text-gray-300'}`} />
                    ))}
                    <span className="text-[10px] text-brand-muted ml-1">
                      {new Date(rev.createdAt).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <h5 className="text-xs font-bold text-brand-dark">{rev.title}</h5>
                <p className="text-xs text-brand-muted mt-1 leading-relaxed">{rev.comment}</p>
              </div>

              {rev.brandResponse && (
                <div className="p-3 rounded-2xl bg-[#F8F7F4] border border-[#E2E1DC] text-xs border-l-4 border-l-[#111312] space-y-1">
                  <span className="font-bold text-[#111312]">Official response from {rev.brandResponse.responderName}:</span>
                  <p className="text-brand-dark">{rev.brandResponse.response}</p>
                </div>
              )}
            </Card>
          ))}
        </div>

      </div>

    </div>
  );
};
