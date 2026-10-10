import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { AuthProvider } from './context/AuthContext';
import { BrandProvider } from './context/BrandContext';
import { NotificationProvider } from './context/NotificationContext';
import { ToastContainer } from './components/ui/Toast';

// Layouts
import { BrandOwnerLayout } from './layouts/BrandOwnerLayout';
import { CustomerLayout } from './layouts/CustomerLayout';

// Landing Page & Auth Screens
import { LandingPage } from './features/landing/LandingPage';
import { WelcomePage } from './features/auth/WelcomePage';
import { CustomerSignIn } from './features/auth/CustomerSignIn';
import { CustomerSignUp } from './features/auth/CustomerSignUp';
import { PhoneOtpVerification } from './features/auth/PhoneOtpVerification';
import { BrandSignIn } from './features/auth/BrandSignIn';
import { BrandRegister } from './features/auth/BrandRegister';
import { BrandVerificationPending } from './features/auth/BrandVerificationPending';
import { PasswordReset } from './features/auth/PasswordReset';

// Brand Owner 13 Core Features
import { OverviewDashboard } from './features/brand-owner/OverviewDashboard'; // 1. Dashboard
import { ThreatOverviewPage } from './features/brand-owner/ThreatOverviewPage'; // 2. Threat Overview
import { ThreatManagementPage } from './features/brand-owner/ThreatManagementPage'; // 3. Threat Management
import { ThreatDetailPage } from './features/brand-owner/ThreatDetailPage'; // 4. Threat Details
import { ThreatCampaignsPage } from './features/brand-owner/ThreatCampaignsPage'; // 5. Campaign Overview
import { CampaignDetailPage } from './features/brand-owner/CampaignDetailPage'; // 6. Campaign Details
import { AlertsPage } from './features/brand-owner/AlertsPage'; // 7. Alerts
import { RiskTrendsPage } from './features/brand-owner/RiskTrendsPage'; // 8. Risk Trends
import { RecommendedActionsPage } from './features/brand-owner/RecommendedActionsPage'; // 9. Recommended Actions
import { AIThreatExplanationPage } from './features/brand-owner/AIThreatExplanationPage'; // 10. AI Threat Explanation
import { ReportsExportPage } from './features/brand-owner/ReportsExportPage'; // 11. Reports
import { BrandProfileSettingsPage } from './features/brand-owner/BrandProfileSettingsPage'; // 12. Brand Profile & Settings
import { CustomerReviewsPage } from './features/brand-owner/CustomerReviewsPage'; // 13. Customer Reviews & Verified Proof

// Customer Pages
import { CustomerHomePage } from './features/customer/CustomerHomePage';
import { TrustedBrandsPage } from './features/customer/TrustedBrandsPage';
import { BrandDetailPage } from './features/customer/BrandDetailPage';
import { SubmitReportPage } from './features/customer/SubmitReportPage';
import { MyReportsPage } from './features/customer/MyReportsPage';
import { CommunityReviewsPage } from './features/customer/CommunityReviewsPage';
import { CustomerProfilePage } from './features/customer/CustomerProfilePage';

const queryClient = new QueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrandProvider>
          <NotificationProvider>
            <BrowserRouter>
              <Routes>
                {/* Main Landing Experience */}
                <Route path="/" element={<LandingPage />} />
                <Route path="/landing" element={<LandingPage />} />
                <Route path="/auth" element={<WelcomePage />} />
                
                {/* Auth Routes */}
                <Route path="/auth/customer-signin" element={<CustomerSignIn />} />
                <Route path="/auth/customer-signup" element={<CustomerSignUp />} />
                <Route path="/auth/verify-otp" element={<PhoneOtpVerification />} />
                <Route path="/auth/brand-login" element={<BrandSignIn />} />
                <Route path="/auth/brand-register" element={<BrandRegister />} />
                <Route path="/auth/brand-verification-pending" element={<BrandVerificationPending />} />
                <Route path="/auth/password-reset" element={<PasswordReset />} />

                {/* Portal A: Brand Owner 12 Core Features */}
                <Route path="/brand-owner" element={<BrandOwnerLayout />}>
                  <Route index element={<Navigate to="/brand-owner/dashboard" replace />} />
                  
                  {/* 1. Dashboard */}
                  <Route path="dashboard" element={<OverviewDashboard />} />
                  <Route path="overview" element={<Navigate to="/brand-owner/dashboard" replace />} />
                  
                  {/* 2. Threat Overview */}
                  <Route path="threat-overview" element={<ThreatOverviewPage />} />
                  
                  {/* 3. Threat Management */}
                  <Route path="threat-management" element={<ThreatManagementPage />} />
                  <Route path="threats" element={<ThreatManagementPage />} />
                  
                  {/* 4. Threat Details */}
                  <Route path="threat-details" element={<ThreatDetailPage />} />
                  <Route path="threat-details/:threatId" element={<ThreatDetailPage />} />
                  <Route path="threats/:threatId" element={<ThreatDetailPage />} />
                  
                  {/* 5. Campaign Overview */}
                  <Route path="campaign-overview" element={<ThreatCampaignsPage />} />
                  <Route path="campaigns" element={<ThreatCampaignsPage />} />
                  
                  {/* 6. Campaign Details */}
                  <Route path="campaign-details" element={<CampaignDetailPage />} />
                  <Route path="campaign-details/:campaignId" element={<CampaignDetailPage />} />
                  <Route path="campaigns/:campaignId" element={<CampaignDetailPage />} />
                  
                  {/* 7. Alerts */}
                  <Route path="alerts" element={<AlertsPage />} />
                  
                  {/* 8. Risk Trends */}
                  <Route path="risk-trends" element={<RiskTrendsPage />} />
                  
                  {/* 9. Recommended Actions */}
                  <Route path="recommended-actions" element={<RecommendedActionsPage />} />
                  
                  {/* 10. AI Threat Explanation */}
                  <Route path="ai-threat-explanation" element={<AIThreatExplanationPage />} />
                  <Route path="ai-explanation" element={<AIThreatExplanationPage />} />
                  
                  {/* 11. Reports */}
                  <Route path="reports" element={<ReportsExportPage />} />
                  
                  {/* 12. Brand Profile & Settings */}
                  <Route path="brand-profile" element={<BrandProfileSettingsPage />} />
                  <Route path="settings" element={<Navigate to="/brand-owner/brand-profile" replace />} />
                  <Route path="identity" element={<Navigate to="/brand-owner/brand-profile" replace />} />
                  
                  {/* 13. Customer Reviews & Verified Proof */}
                  <Route path="reviews" element={<CustomerReviewsPage />} />
                  <Route path="customer-reviews" element={<CustomerReviewsPage />} />
                </Route>

                {/* Portal B: Customer Portal Routes */}
                <Route path="/customer" element={<CustomerLayout />}>
                  <Route index element={<CustomerHomePage />} />
                  <Route path="brands" element={<TrustedBrandsPage />} />
                  <Route path="brands/:brandSlug" element={<BrandDetailPage />} />
                  <Route path="report" element={<SubmitReportPage />} />
                  <Route path="my-reports" element={<MyReportsPage />} />
                  <Route path="reviews" element={<CommunityReviewsPage />} />
                  <Route path="profile" element={<CustomerProfilePage />} />
                </Route>

                {/* Fallback */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>

              <ToastContainer />
            </BrowserRouter>
          </NotificationProvider>
        </BrandProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
