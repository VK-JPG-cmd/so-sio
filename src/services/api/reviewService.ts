import { CustomerReview } from '../../types';
import { MOCK_REVIEWS } from '../mockData';
import { apiClient } from './client';

const REVIEWS_STORAGE_KEY = 'brandshield_customer_reviews';

export const reviewService = {
  getReviews: async (brandId?: string): Promise<CustomerReview[]> => {
    if (!apiClient.isMockMode) {
      try {
        return await apiClient.request<CustomerReview[]>('/reviews', {
          params: brandId ? { brandId } : undefined
        });
      } catch (err) {
        console.warn('Falling back to local reviews', err);
      }
    }

    const stored = localStorage.getItem(REVIEWS_STORAGE_KEY);
    let reviews: CustomerReview[] = stored ? JSON.parse(stored) : MOCK_REVIEWS;
    if (brandId) {
      reviews = reviews.filter(r => r.brandId === brandId);
    }
    return reviews;
  },

  submitReview: async (reviewData: Partial<CustomerReview>): Promise<CustomerReview> => {
    await new Promise(r => setTimeout(r, 500));
    const reviews = await reviewService.getReviews();
    const brand = reviewData.brandName || 'ApexBank Global';

    const newReview: CustomerReview = {
      id: `rev_${Date.now()}`,
      brandId: reviewData.brandId || 'brand_apex_bank',
      brandName: reviewData.brandName || brand,
      userId: reviewData.userId || 'user_cust_1',
      userName: reviewData.userName || 'Verified Customer',
      userPhoneMasked: reviewData.userPhoneMasked || '+1 (555) ***-9921',
      isPhoneVerified: true,
      rating: reviewData.rating || 5,
      title: reviewData.title || 'Verified Product Security Feedback',
      comment: reviewData.comment || 'Verified authentic customer review.',
      createdAt: new Date().toISOString(),
      upvotesCount: 0,
      isCustomerVerifiedOnly: true,
      verifiedProof: reviewData.verifiedProof ? {
        type: reviewData.verifiedProof.type || 'invoice_receipt',
        referenceId: reviewData.verifiedProof.referenceId || `INV-${Date.now().toString().slice(-6)}`,
        proofFileName: reviewData.verifiedProof.proofFileName || 'Customer_Verified_Purchase_Receipt.pdf',
        proofFileUrl: reviewData.verifiedProof.proofFileUrl || 'https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=600&auto=format&fit=crop&q=80',
        verificationTimestamp: new Date().toISOString(),
        verificationStatus: 'verified_authentic',
        proofScore: reviewData.verifiedProof.proofScore || 99,
        orderAmount: reviewData.verifiedProof.orderAmount || '$1,250.00',
        productOrServicePurchased: reviewData.verifiedProof.productOrServicePurchased || 'Official Verified Enterprise Subscription',
        cryptographicHash: reviewData.verifiedProof.cryptographicHash || `0x${Array.from({length: 64}, () => Math.floor(Math.random() * 16).toString(16)).join('')}`
      } : {
        type: 'invoice_receipt',
        referenceId: `INV-${Date.now().toString().slice(-6)}`,
        proofFileName: 'Customer_Verified_Invoice_Proof.pdf',
        proofFileUrl: 'https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=600&auto=format&fit=crop&q=80',
        verificationTimestamp: new Date().toISOString(),
        verificationStatus: 'verified_authentic',
        proofScore: 99,
        orderAmount: '$1,250.00',
        productOrServicePurchased: 'Apex Verified Security & Treasury Services',
        cryptographicHash: `0x${Array.from({length: 64}, () => Math.floor(Math.random() * 16).toString(16)).join('')}`
      }
    };

    const updated = [newReview, ...reviews];
    localStorage.setItem(REVIEWS_STORAGE_KEY, JSON.stringify(updated));
    return newReview;
  },

  respondToReview: async (reviewId: string, responseText: string, responderName: string, responderRole: string): Promise<CustomerReview> => {
    const reviews = await reviewService.getReviews();
    const review = reviews.find(r => r.id === reviewId);
    if (!review) throw new Error('Review not found');

    review.brandResponse = {
      responderName,
      responderRole,
      response: responseText,
      respondedAt: new Date().toISOString()
    };

    localStorage.setItem(REVIEWS_STORAGE_KEY, JSON.stringify(reviews));
    return review;
  },

  upvoteReview: async (reviewId: string): Promise<CustomerReview> => {
    const reviews = await reviewService.getReviews();
    const review = reviews.find(r => r.id === reviewId);
    if (!review) throw new Error('Review not found');

    review.upvotesCount += 1;
    localStorage.setItem(REVIEWS_STORAGE_KEY, JSON.stringify(reviews));
    return review;
  }
};
