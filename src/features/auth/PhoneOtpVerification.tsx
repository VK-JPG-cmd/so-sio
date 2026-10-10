import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { AuthLayout } from '../../layouts/AuthLayout';
import { Button } from '../../components/ui/Button';
import { useAuth } from '../../context/AuthContext';
import { useNotification } from '../../context/NotificationContext';
import { ShieldCheck, RefreshCw } from 'lucide-react';
import confetti from 'canvas-confetti';

import { authService } from '../../services/api/authService';

export const PhoneOtpVerification: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { loginCustomerWithOtp } = useAuth();
  const { showToast } = useNotification();

  const phone = location.state?.phone || '';
  const returnTo = location.state?.returnTo || '/customer';

  // OTP inputs are strictly empty initially - never pre-filled
  const [otp, setOtp] = useState<string[]>(['', '', '', '', '', '']);
  const [timer, setTimer] = useState<number>(60);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isResending, setIsResending] = useState<boolean>(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    // If no phone number in state, redirect back to sign in
    if (!phone) {
      navigate('/auth/customer-signin');
      return;
    }

    // Focus first input on mount
    inputRefs.current[0]?.focus();
    const interval = setInterval(() => {
      setTimer((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [phone, navigate]);

  const handleChange = (index: number, value: string) => {
    // Allow only numeric digits
    const cleaned = value.replace(/\D/g, '');
    if (!cleaned && value) return;

    const newOtp = [...otp];
    newOtp[index] = cleaned.slice(-1);
    setOtp(newOtp);

    // Auto focus next input
    if (cleaned && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace') {
      if (!otp[index] && index > 0) {
        inputRefs.current[index - 1]?.focus();
      }
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (!pasted) return;

    const digits = pasted.split('');
    const newOtp = ['', '', '', '', '', ''];
    digits.forEach((d, i) => {
      newOtp[i] = d;
    });
    setOtp(newOtp);

    const nextIndex = Math.min(digits.length, 5);
    inputRefs.current[nextIndex]?.focus();
  };

  const handleResend = async () => {
    if (timer > 0 || isResending) return;
    setIsResending(true);
    try {
      const res = await authService.startCustomerOtp(phone);
      setTimer(res.cooldown_seconds || 60);
      showToast({ 
        type: 'info', 
        title: 'New Code Dispatched', 
        message: 'A new verification code has been dispatched via SMS. Please check your mobile phone.' 
      });
    } catch (err: any) {
      showToast({ 
        type: 'error', 
        title: 'Resend Failed', 
        message: err.message || 'Please wait before requesting another code.' 
      });
    } finally {
      setIsResending(false);
    }
  };

  const handleVerify = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const code = otp.join('').trim();
    if (code.length < 6) {
      showToast({ 
        type: 'error', 
        title: 'Incomplete Code', 
        message: 'Please enter all 6 digits of the verification code received via SMS.' 
      });
      return;
    }

    setIsLoading(true);
    try {
      await loginCustomerWithOtp(phone, code);
      confetti({
        particleCount: 70,
        spread: 60,
        origin: { y: 0.7 }
      });
      showToast({ 
        type: 'success', 
        title: 'Phone Verified!', 
        message: 'Welcome to So-cio Consumer Protection Portal.' 
      });
      navigate(returnTo);
    } catch (err: any) {
      showToast({ 
        type: 'error', 
        title: 'Verification Failed', 
        message: err.message || 'Invalid or expired verification code. Please check and try again.' 
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout
      mascotPose="celebrating"
      title="Verify Your Phone"
      subtitle="Ensures reliable threat submissions and enables real-time status notifications on investigations."
      badgeText="Two-Factor Security"
      backLink={{ to: '/auth/customer-signin', label: 'Change phone number' }}
    >
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-extrabold text-brand-dark tracking-tight">Enter 6-Digit Code</h2>
          <p className="text-xs text-brand-muted mt-1">
            We sent a verification SMS to <span className="font-semibold text-brand-dark">{phone}</span>
          </p>
        </div>

        {/* 6-Digit Input Row */}
        <form onSubmit={handleVerify} className="space-y-6">
          <div className="flex justify-between gap-2 sm:gap-3">
            {otp.map((digit, idx) => (
              <input
                key={idx}
                ref={(el) => { inputRefs.current[idx] = el; }}
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={1}
                value={digit}
                disabled={isLoading}
                onChange={(e) => handleChange(idx, e.target.value)}
                onKeyDown={(e) => handleKeyDown(idx, e)}
                onPaste={handlePaste}
                className="w-11 h-14 sm:w-14 sm:h-16 text-center text-xl sm:text-2xl font-extrabold rounded-2xl bg-white border border-[#E2E1DC] focus:border-[#111312] focus:ring-2 focus:ring-[#111312]/10 text-brand-dark transition-all duration-200 shadow-sm disabled:opacity-50"
              />
            ))}
          </div>

          <Button
            type="submit"
            className="w-full"
            size="lg"
            isLoading={isLoading}
            disabled={isLoading || otp.join('').length < 6}
            rightIcon={<ShieldCheck className="w-4 h-4" />}
          >
            Verify & Continue
          </Button>
        </form>

        {/* Resend Timer */}
        <div className="flex items-center justify-between pt-2 text-xs text-brand-muted">
          <span>Didn't receive the SMS code?</span>
          <button
            type="button"
            onClick={handleResend}
            disabled={timer > 0 || isResending}
            className={`font-semibold flex items-center gap-1.5 transition-colors ${
              timer > 0 || isResending ? 'text-brand-muted cursor-not-allowed opacity-70' : 'text-[#111312] hover:underline'
            }`}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isResending ? 'animate-spin' : ''}`} />
            {timer > 0 ? `Resend in ${timer}s` : 'Resend Code Now'}
          </button>
        </div>
      </div>
    </AuthLayout>
  );
};
