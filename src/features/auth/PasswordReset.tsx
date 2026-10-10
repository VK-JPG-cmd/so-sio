import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { AuthLayout } from '../../layouts/AuthLayout';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useNotification } from '../../context/NotificationContext';
import { Mail, ArrowRight, CheckCircle2 } from 'lucide-react';

export const PasswordReset: React.FC = () => {
  const [email, setEmail] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { showToast } = useNotification();

  const handleReset = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      setIsSubmitted(true);
      showToast({ type: 'success', title: 'Reset Link Sent', message: `Instructions dispatched to ${email}` });
    }, 600);
  };

  return (
    <AuthLayout
      mascotPose={isSubmitted ? 'celebrating' : 'guarding'}
      title="Reset Password"
      subtitle="Enter your corporate email address to receive a secure single-use recovery link."
      badgeText="Account Recovery"
      backLink={{ to: '/auth/brand-login', label: 'Back to Sign In' }}
    >
      <div className="space-y-5">
        <div>
          <h2 className="text-2xl font-extrabold text-brand-dark tracking-tight">Recover Brand Account</h2>
          <p className="text-xs text-brand-muted mt-1">
            We will verify your organization credentials before sending a password reset token.
          </p>
        </div>

        {!isSubmitted ? (
          <form onSubmit={handleReset} className="space-y-4">
            <Input
              label="Corporate Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="security@yourcompany.com"
              leftIcon={<Mail className="w-4 h-4" />}
              required
            />

            <Button
              type="submit"
              className="w-full"
              size="lg"
              isLoading={isLoading}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Send Password Reset Instructions
            </Button>
          </form>
        ) : (
          <div className="space-y-4 text-center py-4">
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto border border-emerald-200">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h4 className="text-base font-bold text-brand-dark">Check Your Inbox</h4>
              <p className="text-xs text-brand-muted mt-1">
                We've sent a password reset link to <span className="font-semibold text-brand-dark">{email}</span>.
              </p>
            </div>

            <Link to="/auth/brand-login" className="block pt-2">
              <Button variant="outline" className="w-full">
                Return to Brand Sign In
              </Button>
            </Link>
          </div>
        )}
      </div>
    </AuthLayout>
  );
};
