import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthLayout } from '../../layouts/AuthLayout';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useNotification } from '../../context/NotificationContext';
import { Phone, ArrowRight, Sparkles } from 'lucide-react';

import { authService } from '../../services/api/authService';

export const CustomerSignIn: React.FC = () => {
  const [phone, setPhone] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { showToast } = useNotification();

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phone || phone.trim().length < 8) {
      showToast({ type: 'error', title: 'Invalid Phone Number', message: 'Please enter a valid mobile number in international format (e.g. +91 98765 43210).' });
      return;
    }

    setIsLoading(true);
    let normalizedPhone = phone.trim();
    if (!normalizedPhone.startsWith('+')) {
      const digitsOnly = normalizedPhone.replace(/\D/g, '');
      if (digitsOnly.length === 10 && /^[6-9]/.test(digitsOnly)) {
        normalizedPhone = `+91${digitsOnly}`;
      } else if (digitsOnly.length === 10) {
        normalizedPhone = `+1${digitsOnly}`;
      } else if (digitsOnly.length > 10) {
        normalizedPhone = `+${digitsOnly}`;
      }
    }

    try {
      await authService.startCustomerOtp(normalizedPhone);
      showToast({ 
        type: 'success', 
        title: 'Verification Code Requested', 
        message: 'Verification code requested. Check your phone for SMS delivery.' 
      });
      navigate('/auth/verify-otp', { state: { phone: normalizedPhone, returnTo: '/customer' } });
    } catch (err: any) {
      const msg = err.message || 'Failed to dispatch verification code.';
      showToast({ type: 'error', title: 'SMS Delivery Error', message: msg });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout
      mascotPose="waving"
      title="Consumer Protection Portal"
      subtitle="Verify official links, report impersonation scams, and safeguard your personal data."
      badgeText="Phone-Only Secure Authentication"
      backLink={{ to: '/auth', label: 'Choose portal' }}
    >
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-extrabold text-[#111312] tracking-tight">Customer Sign In</h2>
          <p className="text-xs text-[#737478] mt-1">
            We use passwordless SMS verification to keep your account fast and secure.
          </p>
        </div>

        <form onSubmit={handleSendOtp} className="space-y-4">
          <Input
            label="Mobile Phone Number"
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+91 98765 43210 or +1 415 555 2671"
            leftIcon={<Phone className="w-4 h-4" />}
            helperText="Enter your mobile number in international format (+ country code)."
            required
          />

          <Button
            type="submit"
            className="w-full"
            size="lg"
            isLoading={isLoading}
            disabled={isLoading || !phone.trim()}
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            Send Verification Code
          </Button>
        </form>

        <div className="text-center pt-2 text-xs text-[#737478]">
          <span>First time reporting? </span>
          <Link to="/auth/customer-signup" className="font-bold text-[#111312] hover:underline">
            Create an account
          </Link>
        </div>

        <div className="pt-4 border-t border-[#EAE9E4] text-center">
          <Link to="/auth/brand-login" className="text-xs font-semibold text-[#737478] hover:text-[#111312]">
            Are you an enterprise brand owner? <span className="text-[#111312] underline font-bold">Sign in here</span>
          </Link>
        </div>
      </div>
    </AuthLayout>
  );
};
