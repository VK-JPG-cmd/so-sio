import React from 'react';
import { Link } from 'react-router-dom';
import { Mascot, MascotPose } from '../components/ui/Mascot';
import { DemoBadge } from '../components/ui/DemoBadge';
import { Shield, Sparkles, CheckCircle2, ArrowLeft } from 'lucide-react';

interface AuthLayoutProps {
  children: React.ReactNode;
  mascotPose?: MascotPose;
  title: string;
  subtitle: string;
  badgeText?: string;
  features?: string[];
  backLink?: {
    to: string;
    label: string;
  };
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({
  children,
  mascotPose = 'guarding',
  title,
  subtitle,
  badgeText = 'AI Digital Risk Protection',
  features = [
    'Sub-minute domain typosquatting detection',
    'AI-verified social & app impersonation defense',
    'Automated evidence locker & registrar takedowns'
  ],
  backLink = { to: '/auth', label: 'Back to choices' }
}) => {
  return (
    <div className="min-h-screen w-full bg-[#F8F7F4] text-[#111312] p-4 sm:p-6 lg:p-8 flex flex-col justify-between relative">
      {/* Top Navbar */}
      <header className="max-w-7xl w-full mx-auto flex items-center justify-between py-2 z-20">
        <Link to="/" className="flex items-center gap-3 group">
          <img
            src="/socio-logo.png"
            alt="So-cio Logo"
            className="w-10 h-10 object-contain shrink-0 group-hover:scale-105 transition-transform"
          />
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-base font-extrabold text-[#111312] tracking-tight">So-cio</span>
            </div>
            <p className="text-[10px] text-[#737478] font-medium">Digital Risk Protection</p>
          </div>
        </Link>

        <div className="flex items-center gap-3">
          <DemoBadge />
        </div>
      </header>

      {/* Main 2-Panel Composition */}
      <main className="max-w-6xl w-full mx-auto my-auto py-6 sm:py-8 z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
          
          {/* Left Panel: Solid Near-Black High-End Card Inspired by Image 2 */}
          <div className="lg:col-span-5 bg-[#111312] text-white rounded-3xl border border-[#2B2D2C] shadow-2xl p-6 sm:p-8 flex flex-col justify-between space-y-6">
            <div className="space-y-5">
              {backLink && (
                <Link
                  to={backLink.to}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#9A9B9C] hover:text-[#FBF5A5] transition-colors py-1.5 px-3 rounded-full bg-[#1C1E1D] border border-[#2D2F2E]"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>{backLink.label}</span>
                </Link>
              )}

              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#1C1E1D] border border-[#3A3C3B] text-xs font-bold text-[#FBF5A5]">
                <Sparkles className="w-3.5 h-3.5 text-[#FBF5A5]" />
                <span>{badgeText}</span>
              </div>

              <div className="space-y-2">
                <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-tight">
                  {title}
                </h1>
                <p className="text-xs sm:text-sm text-[#9A9B9C] leading-relaxed">
                  {subtitle}
                </p>
              </div>

              {/* 3D Mascot Character */}
              <div className="py-2 flex justify-center">
                <Mascot pose={mascotPose} size="lg" />
              </div>
            </div>

            {/* Value Highlights */}
            {features.length > 0 && (
              <div className="w-full space-y-2.5 pt-4 border-t border-[#262827]">
                {features.map((feat, idx) => (
                  <div key={idx} className="flex items-center gap-2.5 text-xs text-[#D6D6D8] font-medium">
                    <div className="w-5 h-5 rounded-full bg-[#FBF5A5] text-[#111312] flex items-center justify-center shrink-0 font-bold">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    </div>
                    <span>{feat}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right Panel: Clean Solid White Auth Card */}
          <div className="lg:col-span-7 flex">
            <div className="w-full bg-white rounded-3xl border border-[#D5D4CE] shadow-sm p-6 sm:p-10 flex flex-col justify-center">
              {children}
            </div>
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="max-w-7xl w-full mx-auto py-3 text-center text-xs text-[#737478] z-10 flex flex-col sm:flex-row items-center justify-between gap-2 border-t border-[#E2E1DC]">
        <div>&copy; 2026 So-cio &bull; ByteXL Hackathon Edition</div>
        <div className="flex items-center gap-4 text-xs font-semibold text-[#737478]">
          <span className="hover:text-[#111312] cursor-pointer">Security Standards</span>
          <span>&bull;</span>
          <span className="hover:text-[#111312] cursor-pointer">Privacy Guarantee</span>
          <span>&bull;</span>
          <span className="hover:text-[#111312] cursor-pointer">Live Threat Feeds</span>
        </div>
      </footer>
    </div>
  );
};
