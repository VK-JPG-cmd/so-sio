import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthLayout } from '../../layouts/AuthLayout';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useAuth } from '../../context/AuthContext';
import { useNotification } from '../../context/NotificationContext';
import { Mail, Lock, ArrowRight, Sparkles } from 'lucide-react';

export const BrandSignIn: React.FC = () => {
  const [email, setEmail] = useState('elena.rostova@apexbank.com');
  const [password, setPassword] = useState('••••••••••••');
  const [isLoading, setIsLoading] = useState(false);
  const { loginBrandOwner } = useAuth();
  const { showToast } = useNotification();
  const navigate = useNavigate();

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      showToast({ type: 'error', title: 'Missing Email', message: 'Please provide your enterprise corporate email address.' });
      return;
    }

    setIsLoading(true);
    try {
      await loginBrandOwner(email, password);
      showToast({ type: 'success', title: 'Welcome Back, Elena', message: 'ApexBank Global security workspace loaded.' });
      navigate('/brand-owner/overview');
    } catch (err: any) {
      showToast({ type: 'error', title: 'Authentication Failed', message: err.message || 'Invalid credentials' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout
      mascotPose="guarding"
      title="Brand Owner Intelligence"
      subtitle="Defend your brand, stop domain spoofing, and orchestrate rapid registrar takedowns."
      badgeText="Enterprise Security Workspace"
      backLink={{ to: '/auth', label: 'Choose Portal' }}
    >
      <div className="space-y-5">
        <div>
          <h2 className="text-2xl font-extrabold text-[#111312] tracking-tight">Brand Owner Sign In</h2>
          <p className="text-xs text-[#737478] mt-1">
            Access your AI threat feeds, impersonation radars, and takedown workflows.
          </p>
        </div>

        <form onSubmit={handleSignIn} className="space-y-4">
          <Input
            label="Corporate Email Address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="security@yourcompany.com"
            leftIcon={<Mail className="w-4 h-4" />}
            required
          />

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-bold text-[#111312]">Password</label>
              <Link to="/auth/password-reset" className="text-xs font-semibold text-[#111312] hover:text-[#434346] hover:underline">
                Forgot password?
              </Link>
            </div>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your master password"
              leftIcon={<Lock className="w-4 h-4" />}
              required
            />
          </div>

          <Button
            type="submit"
            className="w-full mt-2"
            size="lg"
            isLoading={isLoading}
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            Access Security Dashboard
          </Button>
        </form>

        {/* Demo Fast Login Box */}
        <div className="p-3.5 rounded-xl bg-[#111312] text-white border border-[#2B2D2C] text-xs space-y-1.5">
          <div className="flex items-center justify-between font-bold">
            <span className="flex items-center gap-1.5 text-[#FBF5A5]">
              <Sparkles className="w-3.5 h-3.5 text-[#FBF5A5]" />
              Verified Brand Demo
            </span>
            <button
              type="button"
              onClick={() => {
                setEmail('elena.rostova@apexbank.com');
                setPassword('BrandShieldSecure2026!');
              }}
              className="text-[11px] font-bold text-[#FBF5A5] hover:underline"
            >
              Fill ApexBank Demo
            </button>
          </div>
          <p className="text-[11px] text-[#9A9B9C] leading-snug">
            Loads the fully populated ApexBank enterprise threat workspace.
          </p>
        </div>

        <div className="text-center pt-2 text-xs text-[#737478]">
          <span>New organization? </span>
          <Link to="/auth/brand-register" className="font-bold text-[#111312] hover:underline">
            Register your brand on So-cio
          </Link>
        </div>

        <div className="pt-4 border-t border-[#EAE9E4] text-center">
          <Link to="/auth/customer-signin" className="text-xs font-semibold text-[#737478] hover:text-[#111312]">
            Looking for consumer scam reporting? <span className="text-[#111312] underline font-bold">Go to Customer Portal</span>
          </Link>
        </div>
      </div>
    </AuthLayout>
  );
};
