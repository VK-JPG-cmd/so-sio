import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthLayout } from '../../layouts/AuthLayout';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useNotification } from '../../context/NotificationContext';
import { Phone, User, Mail, ArrowRight, ShieldCheck } from 'lucide-react';
import { authService } from '../../services/api/authService';

export const CustomerSignUp: React.FC = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    consent: true,
  });
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { showToast } = useNotification();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.phone.trim()) {
      showToast({ type: 'error', title: 'Missing Information', message: 'Please provide your full name and mobile number.' });
      return;
    }

    setIsLoading(true);
    try {
      await authService.startCustomerOtp(formData.phone);
      showToast({ 
        type: 'success', 
        title: 'Verification Code Requested', 
        message: 'Verification code requested. Check your phone for SMS delivery.' 
      });
      navigate('/auth/verify-otp', { 
        state: { 
          phone: formData.phone.trim(), 
          name: formData.name.trim(), 
          email: formData.email.trim(),
          returnTo: '/customer' 
        } 
      });
    } catch (err: any) {
      const msg = err.message || 'Failed to dispatch verification code.';
      showToast({ type: 'error', title: 'SMS Delivery Error', message: msg });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout
      mascotPose="celebrating"
      title="Join So-cio Community"
      subtitle="Report suspicious activity and protect millions of consumers worldwide."
      badgeText="Consumer Safety Network"
      backLink={{ to: '/auth/customer-signin', label: 'Back to Sign In' }}
    >
      <div className="space-y-5">
        <div>
          <h2 className="text-2xl font-extrabold text-brand-dark tracking-tight">Create Customer Profile</h2>
          <p className="text-xs text-brand-muted mt-1">
            Sign up in seconds. Phone-verified profiles receive priority investigation triage.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <Input
            label="Full Name"
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="Jane Doe"
            leftIcon={<User className="w-4 h-4" />}
            required
          />

          <Input
            label="Email Address"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="jane.doe@example.com"
            leftIcon={<Mail className="w-4 h-4" />}
            helperText="For receiving investigation updates and resolution alerts."
            required
          />

          <Input
            label="Mobile Phone Number (for OTP)"
            type="tel"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            placeholder="+1 (555) 000-0000"
            leftIcon={<Phone className="w-4 h-4" />}
            helperText="We never sell or spam your phone number."
            required
          />

          <div className="flex items-start gap-2 pt-1">
            <input
              type="checkbox"
              id="consent"
              checked={formData.consent}
              onChange={(e) => setFormData({ ...formData, consent: e.target.checked })}
              className="mt-1 rounded border-brand-border text-[#111312] focus:ring-[#111312]"
              required
            />
            <label htmlFor="consent" className="text-xs text-brand-muted leading-relaxed">
              I agree to the <span className="text-[#111312] font-semibold underline cursor-pointer">Terms of Service</span> and <span className="text-[#111312] font-semibold underline cursor-pointer">Privacy Policy</span>.
            </label>
          </div>

          <Button
            type="submit"
            className="w-full mt-2"
            size="lg"
            isLoading={isLoading}
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            Continue to Phone Verification
          </Button>
        </form>

        <div className="text-center pt-2 text-xs text-brand-muted">
          <span>Already have a customer profile? </span>
          <Link to="/auth/customer-signin" className="font-bold text-[#111312] hover:underline">
            Sign In with OTP
          </Link>
        </div>
      </div>
    </AuthLayout>
  );
};
